import argparse, strformat

var p = newParser:
  help("Test")
  option("-n", "--name", help="A name", required=true)

type 
  Person = object
    name: string

proc greet(self: Person): void =
  echo fmt"Hello, {self.name}"

proc Main(name: string): void =
  let u = Person(name: name)
  u.greet()

when isMainModule:
  try:
    let opts = p.parse()
    Main(opts.name)
  except CatchableError as err:
    echo fmt"Error: {err.msg}"
