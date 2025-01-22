#include <stdio.h>
#include <unistd.h>
#include <stdlib.h>
#include <string.h>
#include <sys/wait.h>
#include <signal.h>

#define HISTORY_SIZE 100 // predefined history size and maximum command length for program to use 
#define CMD_LENGTH 1024

// Combined function to check for input and output redirection
// parses tokens for ">" ensures theres a input/output file/fetches that, populates them and sets the redirtype to 1 for later execution
int check_redirect(char* tokens[], int tokenCount, char **inputFile, char **outputFile) {
    int redirectionType = 0; // 0: none, 1: output, 2: input, 3: both
    for (int i = 0; i < tokenCount; i++) {
        if (strcmp(tokens[i], ">") == 0) {
            if (i + 1 < tokenCount) {
                *outputFile = tokens[i + 1];
                // Remove the redirection token and filename from tokens array
                for (int j = i; j < tokenCount - 2; j++) {
                    tokens[j] = tokens[j + 2];
                }
                tokens[tokenCount - 2] = NULL;
                tokens[tokenCount - 1] = NULL;
                tokenCount -= 2;
                redirectionType |= 1; // sets the redirection output flag
                i--; // Adjust index after removal
            } else {
                fprintf(stderr, "Error: No output file specified\n");
                return -1;
            }
        } else if (strcmp(tokens[i], "<") == 0) {
            if (i + 1 < tokenCount) {
                *inputFile = tokens[i + 1];
                // Remove the redirection token and filename from tokens array
                for (int j = i; j < tokenCount - 2; j++) {
                    tokens[j] = tokens[j + 2];
                }
                tokens[tokenCount - 2] = NULL;
                tokens[tokenCount - 1] = NULL;
                tokenCount -= 2;
                redirectionType |= 2; // Set the input redirection flag
                i--; // Adjust index after removal
            } else {
                fprintf(stderr, "Error: No input file specified\n");
                return -1;
            }
        }
    }
    return redirectionType;
}

void sig_handler(int sign){
    (void)sign;  // here we only print the signal handler/sign , used to indicate when program ends from background
    waitpid(-1, NULL, WNOHANG);
    printf("SIGHANDLER has reaped process %d \n", sign);
}

// Print history
void print_history(char history[][CMD_LENGTH], int history_count) {
    int start = history_count < HISTORY_SIZE ? 0 : history_count % HISTORY_SIZE;
    // ^ this also handles the buffer so when we reach more than 100, it wraps around/still works 

    int count = history_count < HISTORY_SIZE ? history_count : HISTORY_SIZE; // determines how many based on history size, should work for over 100 

    // we do this to avoid overreaching in the history
    // and to prevent null printouts when printinrg
    for (int i = 0; i < count; i++) {
        int index = (start + i) % HISTORY_SIZE;
        printf("%d: %s\n", i + 1, history[index]);
    }
}

void add_to_hist(char* tokens[], int tokensize, char (*history)[CMD_LENGTH], int *history_count) {
    if (tokensize > CMD_LENGTH) {
        fprintf(stderr, "Error: Command too long\n");
        return; // ensure its not long command before adding 
    }

    // Create the command string from tokens
    char command[CMD_LENGTH] = "";
    for (int i = 0; i < tokensize; i++) {
        strcat(command, tokens[i]);
        if (i < tokensize - 1) {
            strcat(command, " ");
        }
    }

    // Add the command to the history
    strcpy(history[*history_count % HISTORY_SIZE], command);

    // Increment the history count
    (*history_count)++;
}




int main(void) {
    char* cwd; //this is a pointer to a char array which will contain the current working directory
    char buff[1024]; //this is the char array which will contain the current working directory
    // set up sig handler
    signal(SIGCHLD, sig_handler); // this is signal.h and handles the signal of child process ending
    char history[HISTORY_SIZE][CMD_LENGTH]; //array to store history of commands
    int history_count = 0; // number of commands in history
    
    while (1) {
        cwd = getcwd(buff, sizeof(buff));
        if (cwd != NULL) {
            printf("%s>", cwd);
        } else {
            perror("getcwd() error"); //perror is a function that prints an error message to stderr(we can look at the unix bootcamp to see what it is)
            return 1;
        }
        char input[1024]; //this is an array to store the input line
        char *tokens[1024]; //pointers to store individual tokens
        int tokenCount = 0; //number of tokens
        if (fgets(input, sizeof(input), stdin) != NULL) {
            if (input[0] == '\n') {
                continue;
            }
            char *parse;
            parse = strtok(input, " \n");
            while (parse != NULL) {
                tokens[tokenCount] = parse;
                tokenCount++;
                parse = strtok(NULL, " \n");
            }
        } else {
            perror("fgets() error");
            return 1;
        }
        input[strcspn(input, "\n")] = '\0';   
        tokens[tokenCount] = NULL;
        // check if background process was called/marked as &
        int isBackground = 0;
        if (tokenCount > 0 && strcmp(tokens[tokenCount - 1], "&") == 0) {
            isBackground = 1;
            tokens[tokenCount - 1] = NULL;
            tokenCount--; // remove from list 
            printf("Background process requested...\n");
        }
        // Check if the first token is "exit"
        if (tokenCount > 0 && strcmp(tokens[0], "exit") == 0) {
            break;
        }
        else if (tokenCount > 0 && strcmp(tokens[0], "history") == 0) {
            // for (int i = 0; i < history_count; i++) {
            //         printf("%d: %s\n", i + 1, history[i]);
            // }   

            print_history(history,history_count);         
            continue;   
        }
        else if (tokenCount > 0 && tokens[0][0] == '!') {
            int index = atoi(&tokens[0][1]); // check if it starts with ! and then get the number
            // atoi converts a string to an integer
            
            if (index > 0 && index <= history_count) {
                // check if valid int 
                strcpy(input, history[index-1]); // copy the command from history to input
                tokenCount = 0;
                printf("Executing from history: %s at index %d from %d\n", input,index-1,index);
                // reset tk count
                char *parse = strtok(input, " \n"); // parse the input  
                while (parse != NULL) {
                    tokens[tokenCount] = parse;
                    tokenCount++;
                    parse = strtok(NULL, " \n"); // get the next token
                }
                tokens[tokenCount] = NULL; // set the last token to null
            } else {
                fprintf(stderr, "Invalid history index\n");
                continue;
            }
        }

        add_to_hist(tokens, tokenCount, history, &history_count); // add to history

        // Check if the first token is "cd"
        if (tokenCount > 0 && strcmp(tokens[0], "cd") == 0) {
            if (tokenCount < 2) {
                fprintf(stderr, "cd: missing argument\n");
            } else {
                if (chdir(tokens[1]) != 0) {
                    perror("cd error");
                }
            }
            continue;
        }
        
        char *inputFile = NULL;
        char *outputFile = NULL;
        int redirectionType = check_redirect(tokens, tokenCount, &inputFile, &outputFile);
        if (redirectionType == -1) {
            continue;
        }
        pid_t pid = fork(); // we fork and execute programs accordingly
        if (pid == -1) {
            perror("fork() error");
            return 1;
        } else if (pid == 0) { 
            if (redirectionType & 2) { // if we have < or > we handle it with fropen 
                if (freopen(inputFile, "r", stdin) == NULL) {
                    perror("freopen() error for input redirection");
                    return 1;
                }
            }
            if (redirectionType & 1) {
                if (freopen(outputFile, "w", stdout) == NULL) {
                    perror("freopen() error for output redirection");
                    return 1;
                }
            }
            execvp(tokens[0], tokens); // then execute command if not <> 
            perror("execvp() error, command may not exist");
            return 1;
        } else { 
            if (!isBackground) { // after executing if not background we waitpid until done
                int status;
                printf("Parent waiting for child to complete...\n");
                waitpid(pid, &status, 0);
                if (WIFEXITED(status)) {
                    int exit_status = WEXITSTATUS(status);
                    if (exit_status == 0) {
                        printf("Child exited with status %d\n", exit_status);
                    } else {
                        printf("Child exited with non-zero status %d\n", exit_status);
                    }
                } else {
                    printf("Child process did not exit normally\n");
                }
            } else { // else we just print/its automatically in background
                printf("Background process started with PID %d\n", pid);
            }
        }
    }

    printf("Closing shell....\n");
    return 0;
}