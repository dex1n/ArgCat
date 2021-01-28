#!/usr/bin/python

from argcat import ArgCat

def test1():
    print("test1")

def test2():
    print("test2")

def test_main():
    print("test_main")

def main():
    argcat = ArgCat()
    argcat.load("argnifest.yml")
    argcat.parse()
    
if __name__ == '__main__':
    main()