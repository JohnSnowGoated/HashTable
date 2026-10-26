#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <errno.h>

#define BUCKET_COUNT 53
#define HASH_PRIME_1 151
#define HASH_PRIME_2 163
#define GRID_COLUMNS 9
#define INPUT_ID 1001
#define INSERT_ID 1002
#define SEARCH_ID 1003
#define DELETE_ID 1004
#define CLEAR_ID 1005
#define STATUS_ID 1006
#define TRACE_ID 1007
#define GRID_ID 1008

typedef enum {
    SLOT_EMPTY,
    SLOT_USED,
    SLOT_DELETED
} slot_state;

typedef struct {
    int64_t value;
    slot_state state;
} bucket;

static bucket g_buckets[BUCKET_COUNT];
static int g_probe_indices[BUCKET_COUNT];
static int g_probe_count;
static int g_active_index = -1;
static HWND g_input;
static HWND g_status;
static HWND g_trace;
static HWND g_grid;

static int hash_string(const char* text, int prime) {
    unsigned int hash = 0;
    for (const unsigned char* p = (const unsigned char*)text; *p; ++p) {
        hash = (hash * (unsigned int)prime + *p) % BUCKET_COUNT;
    }
    return (int)hash;
}

static int hash_index(int attempt, int hash_a, int hash_b) {
    return (hash_a + attempt * (hash_b + 1)) % BUCKET_COUNT;
}

static void set_status(const char* message) {
    SetWindowTextA(g_status, message);
}

static void append_trace(char* trace, size_t capacity, size_t* length,
                         const char* format, ...) {
    if (*length >= capacity) {
        return;
    }

    va_list args;
    va_start(args, format);
    int written = vsnprintf(trace + *length, capacity - *length, format, args);
    va_end(args);

    if (written > 0) {
        size_t available = capacity - *length;
        *length += (size_t)written < available ? (size_t)written : available - 1;
    }
}

static int read_number(char* text, size_t capacity, int64_t* result) {
    char* end = NULL;
    int input_length = GetWindowTextLengthA(g_input);
    if (input_length >= (int)capacity) {
        set_status("Enter an integer with at most 20 characters.");
        return 0;
    }
    GetWindowTextA(g_input, text, (int)capacity);
    if (text[0] == '\0') {
        set_status("Enter an integer first.");
        return 0;
    }

    for (const char* p = text; *p; ++p) {
        if (*p == ' ' || *p == '\t' || *p == '\r' || *p == '\n') {
            set_status("Enter one integer without spaces.");
            return 0;
        }
    }

    errno = 0;
    long long value = strtoll(text, &end, 10);
    if (end == text || *end != '\0' || errno == ERANGE) {
        set_status("That is not a valid integer.");
        return 0;
    }

    *result = (int64_t)value;
    return 1;
}

static void clear_probes(void) {
    g_probe_count = 0;
    g_active_index = -1;
}

static int add_probe(int index) {
    if (g_probe_count >= BUCKET_COUNT) {
        return 0;
    }
    g_probe_indices[g_probe_count++] = index;
    g_active_index = index;
    return 1;
}

static void show_hash_header(char* trace, size_t capacity, size_t* length,
                             const char* text, int hash_a, int hash_b) {
    append_trace(trace, capacity, length,
                 "Input as text: %s\r\n"
                 "h1 = polynomial hash using 151, mod 53 = %d\r\n"
                 "h2 = polynomial hash using 163, mod 53 = %d\r\n"
                 "index(k) = (h1 + k * (h2 + 1)) mod 53\r\n"
                 "Probe step = %d\r\n\r\n",
                 text, hash_a, hash_b, hash_b + 1);
}

static void perform_operation(int operation) {
    char text[32];
    char trace[8192] = "";
    size_t length = 0;
    int64_t value;
    int hash_a;
    int hash_b;
    int found = 0;
    int first_deleted = -1;

    if (!read_number(text, sizeof(text), &value)) {
        return;
    }

    clear_probes();
    hash_a = hash_string(text, HASH_PRIME_1);
    hash_b = hash_string(text, HASH_PRIME_2);
    show_hash_header(trace, sizeof(trace), &length, text, hash_a, hash_b);

    for (int attempt = 0; attempt < BUCKET_COUNT; ++attempt) {
        int index = hash_index(attempt, hash_a, hash_b);
        bucket* slot = &g_buckets[index];
        add_probe(index);

        if (slot->state == SLOT_EMPTY) {
            append_trace(trace, sizeof(trace), &length,
                         "Attempt %d -> bucket %02d: empty\r\n", attempt, index);
            if (operation == INSERT_ID) {
                int destination = first_deleted >= 0 ? first_deleted : index;
                g_buckets[destination].value = value;
                g_buckets[destination].state = SLOT_USED;
                if (first_deleted >= 0) {
                    set_status("Inserted the number into the first available probe bucket (reusing a deleted slot).");
                    g_active_index = destination;
                } else {
                    set_status("Inserted the number into the first empty bucket.");
                }
            } else if (operation == SEARCH_ID) {
                set_status("Number not found; search stopped at the first empty bucket.");
            } else {
                set_status("Number not found.");
            }
            found = 1;
            break;
        }

        if (slot->state == SLOT_DELETED) {
            append_trace(trace, sizeof(trace), &length,
                         "Attempt %d -> bucket %02d: deleted slot\r\n", attempt, index);
            if (operation == INSERT_ID && first_deleted < 0) {
                first_deleted = index;
            }
            continue;
        }

        append_trace(trace, sizeof(trace), &length,
                     "Attempt %d -> bucket %02d: contains %lld\r\n",
                     attempt, index, (long long)slot->value);
        if (slot->value == value) {
            if (operation == DELETE_ID) {
                slot->state = SLOT_DELETED;
                set_status("Number deleted; its bucket is marked as a tombstone.");
            } else if (operation == INSERT_ID) {
                set_status("That number is already in the table.");
            } else {
                set_status("Number found in the table.");
            }
            found = 1;
            break;
        }

    }

    if (!found && operation == INSERT_ID && first_deleted >= 0) {
        g_buckets[first_deleted].value = value;
        g_buckets[first_deleted].state = SLOT_USED;
        g_active_index = first_deleted;
        set_status("Inserted the number into a previously deleted bucket.");
        found = 1;
    }

    if (!found && operation == INSERT_ID) {
        set_status("The table is full; the number could not be inserted.");
    } else if (!found) {
        set_status("No matching number was found after checking all buckets.");
    }

    append_trace(trace, sizeof(trace), &length, "\r\nThe highlighted buckets show this operation's probe path.");
    SetWindowTextA(g_trace, trace);
    InvalidateRect(g_grid, NULL, TRUE);
}

static void set_font(HWND control, HFONT font) {
    SendMessageA(control, WM_SETFONT, (WPARAM)font, TRUE);
}

static HWND create_control(HWND parent, const char* class_name, const char* text,
                           DWORD style, int x, int y, int width, int height,
                           int id, HFONT font) {
    HWND control = CreateWindowExA(
        0, class_name, text, WS_CHILD | WS_VISIBLE | style,
        x, y, width, height, parent, (HMENU)(INT_PTR)id,
        GetModuleHandleA(NULL), NULL);
    if (control) {
        set_font(control, font);
    }
    return control;
}

static void draw_grid(HWND window, HDC dc) {
    RECT client;
    GetClientRect(window, &client);
    FillRect(dc, &client, (HBRUSH)(COLOR_WINDOW + 1));

    HFONT font = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
    HFONT old_font = (HFONT)SelectObject(dc, font);
    SetBkMode(dc, TRANSPARENT);

    int width = client.right / GRID_COLUMNS;
    int height = 54;
    for (int i = 0; i < BUCKET_COUNT; ++i) {
        int row = i / GRID_COLUMNS;
        int col = i % GRID_COLUMNS;
        RECT cell = {
            col * width + 3,
            row * height + 3,
            (col + 1) * width - 3,
            (row + 1) * height - 3
        };
        COLORREF color = RGB(241, 245, 249);

        if (g_buckets[i].state == SLOT_USED) {
            color = RGB(219, 234, 254);
        } else if (g_buckets[i].state == SLOT_DELETED) {
            color = RGB(254, 243, 199);
        }
        for (int p = 0; p < g_probe_count; ++p) {
            if (g_probe_indices[p] == i) {
                color = (i == g_active_index) ? RGB(187, 247, 208) : RGB(254, 215, 170);
                break;
            }
        }

        HBRUSH brush = CreateSolidBrush(color);
        FillRect(dc, &cell, brush);
        DeleteObject(brush);
        FrameRect(dc, &cell, (HBRUSH)GetStockObject(GRAY_BRUSH));

        char label[48];
        if (g_buckets[i].state == SLOT_USED) {
            snprintf(label, sizeof(label), "%02d: %lld", i,
                     (long long)g_buckets[i].value);
        } else if (g_buckets[i].state == SLOT_DELETED) {
            snprintf(label, sizeof(label), "%02d: deleted", i);
        } else {
            snprintf(label, sizeof(label), "%02d: empty", i);
        }

        SetTextColor(dc, RGB(30, 41, 59));
        DrawTextA(dc, label, -1, &cell, DT_CENTER | DT_VCENTER | DT_SINGLELINE);
    }
    SelectObject(dc, old_font);
}

static LRESULT CALLBACK grid_window_proc(HWND window, UINT message,
                                         WPARAM w_param, LPARAM l_param) {
    if (message == WM_PAINT) {
        PAINTSTRUCT paint;
        HDC dc = BeginPaint(window, &paint);
        draw_grid(window, dc);
        EndPaint(window, &paint);
        return 0;
    }
    return DefWindowProcA(window, message, w_param, l_param);
}

static void create_interface(HWND window) {
    HFONT font = (HFONT)GetStockObject(DEFAULT_GUI_FONT);
    HFONT title_font = CreateFontA(
        26, 0, 0, 0, FW_BOLD, FALSE, FALSE, FALSE, DEFAULT_CHARSET,
        OUT_DEFAULT_PRECIS, CLIP_DEFAULT_PRECIS, CLEARTYPE_QUALITY,
        DEFAULT_PITCH | FF_DONTCARE, "Segoe UI");
    if (!title_font) {
        title_font = font;
    }

    HWND title = create_control(window, "STATIC", "Double Hashing Visualizer",
                                SS_LEFT, 24, 18, 600, 36, 0, title_font);
    (void)title;
    create_control(window, "STATIC",
                   "Enter an integer to see its hash values, probe sequence, and table location.",
                   SS_LEFT, 26, 58, 900, 24, 0, font);
    create_control(window, "STATIC", "Number:", SS_LEFT, 26, 99, 70, 24, 0, font);
    g_input = create_control(window, "EDIT", "", WS_BORDER | ES_AUTOHSCROLL,
                             92, 95, 250, 28, INPUT_ID, font);
    create_control(window, "BUTTON", "Insert", BS_PUSHBUTTON,
                   356, 94, 86, 30, INSERT_ID, font);
    create_control(window, "BUTTON", "Search", BS_PUSHBUTTON,
                   450, 94, 86, 30, SEARCH_ID, font);
    create_control(window, "BUTTON", "Delete", BS_PUSHBUTTON,
                   544, 94, 86, 30, DELETE_ID, font);
    create_control(window, "BUTTON", "Clear table", BS_PUSHBUTTON,
                   638, 94, 100, 30, CLEAR_ID, font);

    g_status = create_control(window, "STATIC", "Ready.", SS_LEFT,
                              26, 137, 900, 25, STATUS_ID, font);
    create_control(window, "STATIC", "53 buckets (prime table size)",
                   SS_LEFT, 26, 173, 600, 24, 0, font);

    WNDCLASSA grid_class = {0};
    grid_class.lpfnWndProc = grid_window_proc;
    grid_class.hInstance = GetModuleHandleA(NULL);
    grid_class.lpszClassName = "HashVisualizerGrid";
    grid_class.hCursor = LoadCursorA(NULL, IDC_ARROW);
    grid_class.hbrBackground = (HBRUSH)(COLOR_WINDOW + 1);
    RegisterClassA(&grid_class);

    g_grid = CreateWindowExA(WS_EX_CLIENTEDGE, grid_class.lpszClassName, "",
                             WS_CHILD | WS_VISIBLE,
                             24, 199, 648, 324, window, (HMENU)(INT_PTR)GRID_ID,
                             GetModuleHandleA(NULL), NULL);

    create_control(window, "STATIC", "Hash calculation and probe trace",
                   SS_LEFT, 697, 173, 300, 24, 0, font);
    g_trace = create_control(
        window, "EDIT", "Enter a number and choose Insert, Search, or Delete.",
        WS_BORDER | ES_MULTILINE | ES_READONLY | ES_AUTOVSCROLL | WS_VSCROLL,
        697, 199, 355, 324, TRACE_ID, font);
    SendMessageA(g_trace, EM_SETLIMITTEXT, 8191, 0);

    create_control(window, "STATIC",
                   "Green = active probe   Orange = earlier probe   Blue = stored number   Yellow = deleted slot",
                   SS_LEFT, 26, 535, 1030, 24, 0, font);

    if (title_font != font) {
        SendMessageA(title, WM_SETFONT, (WPARAM)title_font, TRUE);
    }
}

static LRESULT CALLBACK main_window_proc(HWND window, UINT message,
                                         WPARAM w_param, LPARAM l_param) {
    switch (message) {
        case WM_CREATE:
            create_interface(window);
            return 0;

        case WM_COMMAND:
            switch (LOWORD(w_param)) {
                case INSERT_ID:
                case SEARCH_ID:
                case DELETE_ID:
                    if (HIWORD(w_param) == BN_CLICKED) {
                        perform_operation(LOWORD(w_param));
                    }
                    return 0;
                case CLEAR_ID:
                    if (HIWORD(w_param) == BN_CLICKED) {
                        memset(g_buckets, 0, sizeof(g_buckets));
                        clear_probes();
                        SetWindowTextA(g_trace, "The table is empty. Enter a number to begin.");
                        set_status("Table cleared.");
                        InvalidateRect(g_grid, NULL, TRUE);
                    }
                    return 0;
            }
            break;

        case WM_GETMINMAXINFO: {
            MINMAXINFO* info = (MINMAXINFO*)l_param;
            info->ptMinTrackSize.x = 1090;
            info->ptMinTrackSize.y = 620;
            return 0;
        }

        case WM_DESTROY:
            PostQuitMessage(0);
            return 0;
    }
    return DefWindowProcA(window, message, w_param, l_param);
}

int WINAPI WinMain(HINSTANCE instance, HINSTANCE previous, LPSTR command_line, int show) {
    (void)previous;
    (void)command_line;

    WNDCLASSA window_class = {0};
    window_class.lpfnWndProc = main_window_proc;
    window_class.hInstance = instance;
    window_class.lpszClassName = "HashVisualizerWindow";
    window_class.lpszMenuName = NULL;
    window_class.hCursor = LoadCursorA(NULL, IDC_ARROW);
    window_class.hbrBackground = (HBRUSH)(COLOR_BTNFACE + 1);
    window_class.style = CS_HREDRAW | CS_VREDRAW;

    if (!RegisterClassA(&window_class)) {
        MessageBoxA(NULL, "Could not register the application window.",
                    "Hash Visualizer", MB_ICONERROR | MB_OK);
        return 1;
    }

    HWND window = CreateWindowExA(
        0, window_class.lpszClassName, "Hash Table Number Visualizer",
        WS_OVERLAPPEDWINDOW, CW_USEDEFAULT, CW_USEDEFAULT, 1150, 620,
        NULL, NULL, instance, NULL);
    if (!window) {
        MessageBoxA(NULL, "Could not create the application window.",
                    "Hash Visualizer", MB_ICONERROR | MB_OK);
        return 1;
    }

    ShowWindow(window, show);
    UpdateWindow(window);

    MSG message;
    while (GetMessageA(&message, NULL, 0, 0) > 0) {
        TranslateMessage(&message);
        DispatchMessageA(&message);
    }
    return (int)message.wParam;
}
