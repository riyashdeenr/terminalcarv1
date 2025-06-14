# calculator.py
print("Enter operation (e.g., 2+3):")
while True:
    try:
        expr = input("> ")
        print(f"Result: {eval(expr)}")
    except:
        print("Invalid input")
