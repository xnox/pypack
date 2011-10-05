from pypack_test.circular_1 import c1

def print_hello():
    print "hello from c2"

def main():
    c1.print_hello()
    print_hello()

if __name__ == "__main__":
    main()
