CC = gcc
CFLAGS ?= -std=gnu11 -Wall -Wextra -O2
GUI_TARGET ?= hash_visualizer.exe
CONSOLE_TARGET ?= hash_table.exe

ifeq ($(OS),Windows_NT)
RM = cmd /c del /Q
else
RM = rm -f
endif

.PHONY: all run gui console run-console clean

all: $(GUI_TARGET)

$(GUI_TARGET): hash_visualizer.c
	$(CC) $(CFLAGS) -mwindows -o $@ $< -luser32 -lgdi32

$(CONSOLE_TARGET): hash_table.c
	$(CC) $(CFLAGS) -o $@ $< -lm

gui: $(GUI_TARGET)

console: $(CONSOLE_TARGET)

run: $(GUI_TARGET)
	./$(GUI_TARGET)

run-console: $(CONSOLE_TARGET)
	./$(CONSOLE_TARGET)

clean:
	$(RM) $(GUI_TARGET) $(CONSOLE_TARGET)
