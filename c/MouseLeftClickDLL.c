// clicker_dll.c
#include <windows.h>

void send_left_click(int x, int y)
{
    // Set cursor position
    SetCursorPos(x, y);

    // Prepare INPUT structures
    INPUT inputs[2] = {0};

    inputs[0].type = INPUT_MOUSE;
    inputs[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN;

    inputs[1].type = INPUT_MOUSE;
    inputs[1].mi.dwFlags = MOUSEEVENTF_LEFTUP;

    // Send click
    SendInput(2, inputs, sizeof(INPUT));
}

BOOL APIENTRY DllMain(HMODULE hModule,
    DWORD  ul_reason_for_call,
    LPVOID lpReserved
)
{
    if (ul_reason_for_call == DLL_PROCESS_ATTACH)
    {
        // Example: click at (500, 500)
        send_left_click(500, 500);
    }
    return TRUE;
}
