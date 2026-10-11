#include <stdio.h>
#include <string.h>

#define ACCOUNT_COUNT 3
#define ACCOUNT_NUMBER_SIZE 12
#define INPUT_SIZE 100

/* C owns the account data for as long as this engine process is running. */
char accountNumbers[ACCOUNT_COUNT][ACCOUNT_NUMBER_SIZE] = {
    "10010001", "10010002", "10010003"
};
int accountPins[ACCOUNT_COUNT] = {1234, 2468, 1357};
float accountBalances[ACCOUNT_COUNT] = {2500.00f, 5000.00f, 1250.50f};

int findAccount(char accountNumber[]) {
    int index;
    for (index = 0; index < ACCOUNT_COUNT; index++) {
        if (strcmp(accountNumber, accountNumbers[index]) == 0) {
            return index;
        }
    }
    return -1;
}

int main(void) {
    char input[INPUT_SIZE];
    char command[16];
    char accountNumber[ACCOUNT_NUMBER_SIZE];
    int pin;
    int accountIndex = -1;
    int failedAttempts = 0;
    float amount;

    /* Flask sends one text command per line and reads one reply per command. */
    while (fgets(input, INPUT_SIZE, stdin) != NULL) {
        command[0] = '\0';
        accountNumber[0] = '\0';

        if (sscanf(input, "%15s", command) != 1) {
            printf("ERR|Empty command\n");
        } else if (strcmp(command, "LOGIN") == 0) {
            if (failedAttempts >= 3) {
                printf("ERR|Too many incorrect attempts. Restart the server to unlock.\n");
            } else if (sscanf(input, "%15s %11s %d", command, accountNumber, &pin) != 3) {
                failedAttempts++;
                printf("ERR|Enter an account number and 4-digit PIN.\n");
            } else {
                int foundIndex = findAccount(accountNumber);
                if (foundIndex < 0 || pin != accountPins[foundIndex]) {
                    failedAttempts++;
                    if (failedAttempts >= 3) {
                        printf("ERR|Too many incorrect attempts. Restart the server to unlock.\n");
                    } else {
                        printf("ERR|Account number or PIN is incorrect.\n");
                    }
                } else {
                    accountIndex = foundIndex;
                    failedAttempts = 0;
                    printf("OK|%s|%.2f\n", accountNumbers[accountIndex], accountBalances[accountIndex]);
                }
            }
        } else if (strcmp(command, "BALANCE") == 0) {
            if (accountIndex < 0) {
                printf("ERR|Please sign in again.\n");
            } else {
                printf("OK|%.2f\n", accountBalances[accountIndex]);
            }
        } else if (strcmp(command, "DEPOSIT") == 0 || strcmp(command, "WITHDRAW") == 0) {
            if (accountIndex < 0) {
                printf("ERR|Please sign in again.\n");
            } else if (sscanf(input, "%15s %f", command, &amount) != 2 || amount <= 0.0f) {
                printf("ERR|Enter an amount greater than zero.\n");
            } else if (strcmp(command, "DEPOSIT") == 0) {
                accountBalances[accountIndex] = accountBalances[accountIndex] + amount;
                printf("OK|%.2f|DEPOSIT\n", accountBalances[accountIndex]);
            } else if (amount > accountBalances[accountIndex]) {
                printf("ERR|Insufficient balance.\n");
            } else {
                accountBalances[accountIndex] = accountBalances[accountIndex] - amount;
                printf("OK|%.2f|WITHDRAW\n", accountBalances[accountIndex]);
            }
        } else if (strcmp(command, "LOGOUT") == 0) {
            accountIndex = -1;
            printf("OK|Logged out\n");
        } else {
            printf("ERR|Unknown command.\n");
        }
        fflush(stdout);
    }
    return 0;
}
