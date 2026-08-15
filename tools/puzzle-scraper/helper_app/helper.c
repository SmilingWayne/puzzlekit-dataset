#include <stdlib.h>
#include <unistd.h>

int main(int argc, char *argv[]) {
    if (argc < 2) {
        return 1;
    }
    execl("/bin/zsh", "zsh", argv[1], (char *)NULL);
    return 1;
}
