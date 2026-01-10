import
  argparse,
  locks,
  logging,
  os,
  std/re,
  strformat,
  system,
  tables,
  winim/core,
  winim/lean

type
  # KEYBDINPUT_STRUCT* = object
  #   wVK*: WORD
  #   wScan*: WORD
  #   dwFlags*: DWORD
  #   time*: DWORD
  #   dwExtraInfo*: ULONG_PTR

  # MOUSEINPUT_STRUCT* = object
  #   dx*: LONG
  #   dy*: LONG
  #   mouseData*: DWORD
  #   dwFlags*: DWORD
  #   time*: DWORD
  #   dwExtraInfo*: ULONG_PTR

  # INPUT_UNION* {.union.} = object
  #   mi*: MOUSEINPUT_STRUCT
  #   ki*: KEYBDINPUT_STRUCT

  # INPUT* = object
  #   `type`*: DWORD
  #   u*: INPUT_UNION

  wchar = uint16

const    
  KEY_PRESS_MASK = 0x8000
  SHIFT_KEY_MASK = 0xFF
  ESC_KEY = 0x1B
  MOUSE_INPUT = 0
  KEYBD_INPUT = 1
  KEYBDEVENTF_KEYDOWN = 0x0000
  KEYBDEVENTF_KEYUP = 0x0002
  MOUSEEVENTF_LEFTDOWN = 0x0002
  MOUSEEVENTF_LEFTUP = 0x0004
  KEYEVENTF_SCANCODE = 0x0008

proc wcslen(s: ptr wchar): int {.importc: "wcslen", dynlib: "msvcrt".}

proc isKeyPressed(virtual_key: int32): bool = 
  try:
    result = (GetAsyncKeyState(virtual_key) and KEY_PRESS_MASK) != 0
  except:
    raise newException(ValueError, &"Invalid virtual key code: {virtual_key}. Please provide a valid hexadecimal key code")

proc getVirtualKey(key: string): int32 = 
  if key.len != 1:
    raise newException(ValueError, &"Key '{key}' must be a single character")

  let ch = key[0]
  if not ch.isAlphaNumeric:
    raise newException(ValueError, &"'{ch}' is not a valid printable alphanumeric character")

  let vk = VkKeyScanW(cast[wchar](ch)) and SHIFT_KEY_MASK

  if vk == SHIFT_KEY_MASK:
    raise newException(ValueError, fmt"Unable to find virtual key for '{key}'")

  result = int32(vk)

proc getKeyName(virtual_key: int32): string = 
  let l_param = MapVirtualKeyW(virtual_key, 0) shl 16
  var buf: array[64, wchar]

  if GetKeyNameTextW(l_param, cast[LPWSTR](addr buf[0]), 64) == 0:
    raise newException(ValueError, &"Could not retrieve name for virtual key {virtual_key}.")

  $buf[0..(wcslen(addr buf[0])-1)]

proc mouseSendInput(flags:DWORD, dx:LONG=0, dy:LONG=0, data:DWORD=0, time:DWORD=0, extraInfo:ULONG_PTR=0): int32 = 
  var input: INPUT
  input.`type` = MOUSE_INPUT
  input.mi.dx = dx
  input.mi.dy = dy
  input.mi.mouseData = data
  input.mi.dwFlags = flags
  input.mi.time = time
  input.mi.dwExtraInfo = extraInfo
  result = SendInput(1, addr input, int32(sizeof(input)))

proc keybdSendInput(flags:DWORD, vk:WORD=0, scan:WORD=0, time:DWORD=0, extraInfo:ULONG_PTR=0): int32 = 
  var input: INPUT
  input.`type` = KEYBD_INPUT
  input.ki.wVK = vk
  input.ki.wScan = scan
  input.ki.dwFlags = flags
  input.ki.time = time
  input.ki.dwExtraInfo = extraInfo
  result = SendInput(1, addr input, int32(sizeof(input)))

proc risingDetection(curr:bool, prev:bool, safemode:bool, safeKeyIsPressed:bool): tuple[curr: bool, prev: bool] =
  if not safemode or safeKeyIsPressed:
    return (curr and not prev, curr)
  else:
    return (false, prev)

const
  DEFAULT_CPS = 24.0
  DEFAULT_START_KEY = "S"
  DEFAULT_PAUSE_KEY = "P"
  DEFAULT_QUIT_KEY = "Q"
  DEFAULT_SAFE_KEY = 0x12 

var parserHandler = newParser:
  help("A simple auto-clicker script that allows you to automate mouse clicks.\nPress 'StartKey' to start/resume clicking, 'PauseKey' to pause, and 'QuitKey' to quit.")
  flag("--no-safemode", hidden=true, help=fmt"Disable safe mode. When enabled, the safe key must be held to start or quit the script to prevent unintended behavior")
  flag("--no-cautions", hidden=true, help=fmt"Disable cautions which can lead to unintended behaviour")
  option("-cps", "--clicks-per-second", default=some($DEFAULT_CPS), help=fmt"Target clicks per second (CPS). Default: '{$DEFAULT_CPS}cps'")
  option("-sk", "--startkey", default=some(DEFAULT_START_KEY), help=fmt"Virtual key to start/resume clicking. Default: '{DEFAULT_START_KEY}'")
  option("-pk", "--pausekey", default=some(DEFAULT_PAUSE_KEY), help=fmt"Virtual key to pause clicking. Default: '{DEFAULT_PAUSE_KEY}'")
  option("-qk", "--quitkey", default=some(DEFAULT_QUIT_KEY), help=fmt"Virtual key to quit the autoclicker. Default: '{DEFAULT_QUIT_KEY}'")
  option("-sf", "--safekey", default=some($DEFAULT_SAFE_KEY), help=fmt"Virtual key to use in safe mode. Default: 0x12 (this shit language doesnt allow me to use the function that converts the int value to the key name.)")


let logFilePath = relativePath(getAppFilename(), getCurrentDir())
var loggerFile = open(replace(logFilePath, re(r"\.exe$"), ".log"), fmAppend)
var loggerHandler = newFileLogger(loggerFile)

type
  Event = object
    lock: Lock
    cond: Cond
    flag: bool

# Event-like behavior
proc initEvent(): Event =
  var e: Event
  initLock(e.lock)
  initCond(e.cond)
  e.flag = false
  return e

proc wait(e: var Event) =
  acquire(e.lock)
  while not e.flag:
    wait(e.cond, e.lock)
  release(e.lock)

proc set(e: var Event) =
  acquire(e.lock)
  e.flag = true
  broadcast(e.cond)
  release(e.lock)

proc clear(e: var Event) =
  acquire(e.lock)
  e.flag = false
  release(e.lock)

proc isSet(e: var Event): bool =
  acquire(e.lock)
  let res = e.flag
  release(e.lock)
  return res

const
  debounceSLEEPTIME: int = 69

type
  Autoclicker = object
    clickThread: Lock
    clickingEvent: Event
    quitEvent: Event

    clicksPerSecond: float64 = 42.0
    startKey: int32 = 0x41
    pauseKey: int32 = 0x42
    quitKey: int32 = 0x43
    safeKey: int32 = 0x12
    safeMode: bool = true
    startState, pauseState, quitState: bool = false

proc setup(self: var Autoclicker, clicksPerSecond: float64, startKey: int32, pauseKey: int32, quitKey: int32, safeKey: int32, safeMode: bool = true): void = 

  if clicksPerSecond <= 0:
    raise newException(ValueError, fmt"{clicksPerSecond} is not a valid value. clicks per second must be a positive real number (unsigned float)")

  if clicksPerSecond > 500:
    raise newException(ValueError, fmt"{clicksPerSecond} is too big")

  var counts = initTable[string, int]()
  for key, val in fieldPairs(self):
    if key.endsWith("Key"):
      counts[$val] = counts.getOrDefault($val, 0)+1
  if any(toSeq(tables.values(counts)), proc(v: int): bool = v!=1):
    raise newException(ValueError, "It is not advised to use the same key for two different actions")

  self.clicksPerSecond = clicksPerSecond
  self.startKey = startKey
  self.pauseKey = pauseKey
  self.quitKey = quitKey
  self.safeKey = safeKey
  self.safeMode = safeMode

proc start(self: var Autoclicker): void =
  stdout.write "Clicking started.".alignLeft(80), "\r"
  stdout.flushFile()
  self.clickingEvent.set()
  sleep(debounceSLEEPTIME)

proc pause(self: var Autoclicker): void =
  stdout.write "Clicking paused.".alignLeft(80), "\r"
  stdout.flushFile()
  self.clickingEvent.clear()
  sleep(debounceSLEEPTIME)

proc quit(self: var Autoclicker): void =
  stdout.write "Quitting...".alignLeft(80), "\r"
  stdout.flushFile()
  self.quitEvent.set()
  sleep(debounceSLEEPTIME)

proc loop (self: var Autoclicker, fun: proc() {.closure.}): void =
  while not self.quitEvent.isSet():
    if self.clickingEvent.isSet():
      try:
        fun()
      except CatchableError as err:
        echo fmt"Error: {err.msg}"
        self.pause()
      finally:
        sleep(int(1000/self.clicksPerSecond))
    else:
      sleep(123)

proc run(self: var Autoclicker, fun: proc() {.closure.}): void =
  echo "Use --help (-h) for usage information."
  if self.safeMode:
    echo "Safemode is enabled. Press the safe key together with start/quit keys to start/quit."
  echo fmt"Press '{getKeyName(self.startKey)}' to start/resume clicking, '{getKeyName(self.pauseKey)}' to pause, and '{getKeyName(self.quitKey)}' to quit. CPS: {self.clicksPerSecond}/sec"

  while not self.quitEvent.isSet():
    let safeKeyIsPressed = isKeyPressed(self.safeKey)

    let (startEdge, newStartState) = risingDetection(isKeyPressed(self.startKey), self.startState, self.safeMode, safeKeyIsPressed)
    self.startState = newStartState
    if not self.clickingEvent.isSet() and startEdge:
      self.start()

    let (pauseEdge, newPauseState) = risingDetection(isKeyPressed(self.pauseKey), self.pauseState, self.safeMode, true)
    self.pauseState = newPauseState
    if self.clickingEvent.isSet() and pauseEdge:
      self.pause()

    let (quitEdge, newQuitState) = risingDetection(isKeyPressed(self.quitKey), self.quitState, self.safeMode, safeKeyIsPressed)
    self.quitState = newQuitState
    if quitEdge:
      self.quit()
      break

    if self.clickingEvent.isSet():
      try:
        fun()
      except CatchableError as err:
        echo fmt"An error occurred: {err.msg}"
        self.pause()

    sleep(debounceSLEEPTIME)

when isMainModule:

  var autoclicker: ref Autoclicker = nil

  try:
    let args = parserHandler.parse()
    new(autoclicker)
    autoclicker[] = Autoclicker(
      clickingEvent: initEvent(),
      quitEvent: initEvent(),
      clicksPerSecond: parseFloat(args.clicksPerSecond),
      startKey: getVirtualKey(args.startkey),
      pauseKey: getVirtualKey(args.pausekey),
      quitKey: getVirtualKey(args.quitkey),
      safeKey: getVirtualKey(args.safekey),
      safeMode: args.nosafemode
    )
    # loggerFile.log(lvlInfo, "The script have been initialized and fuck any other information because this language sucks and I cant make anything work")
    

  except ShortCircuit as sc:
    if sc.flag == "argparse_help":
      echo sc.help
      quit(0)
    else:
      echo fmt"Unexpected ShortCircuit: {sc.flag}"
      loggerHandler.log(lvlError, fmt"A ShortCircuit occured: {sc.msg}")
      quit(1)

  except CatchableError as err:
    echo fmt"Error: {err.msg}"
    loggerHandler.log(lvlError, fmt"An error occured: {err.msg}")
    quit(1)