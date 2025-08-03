```Ruby
def fact(num)
    fat = 1
    until num == 0 
        fat *= num
        num -= 1
    end
    fat
end

(0..172).each do |num|
    p "The factorial of #{num} is #{fact(num)}."
end

def fact(num)
    fat = 1
    (1..num).each do |n|
        fat *= n
    end
    fat
end
```

```Haskell
fact :: Integer -> Integer
fact number = product [1..number]

fact2Str :: Integer -> String
fact2Str number = "The factorial of " ++ show number ++ " is " ++ show (fact number) ++ "."

main = mapM_ print(map fact2Str [1..172])
```

```JavaScript
function fact(num)
{
    return new Array(num).fill(0).map((_, i) => i+1).reduce((fat, num) => fat * num, 1);
}
new Array(172).fill(0).map((_, i) => console.log(`The factorial of ${i} is ${fact(i)}.`));

function fact(num)
{
    return Array.from({length: num}, (_, i) => i+1).reduce((fat, num) => fat * num, 1);
}
Array.from({length: 172}, (_, i) => console.log(`The factorial of ${i} is ${fact(i)}.`));
```

```Python
def fact(num):
    if num <= 1:
        return 1
    return num * fact(num - 1)

for num in range(0, 172):
    print("The factorial of {} is {}.".format(num, fact(num)))
```