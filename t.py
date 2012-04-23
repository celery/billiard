import billiard


def f(x):
    print("PROCESS %r" % (x, ))
    return x ** x


def cb(res):
    print("GOT: %r" % (res, ))



def main():
    billiard.forking_enable(False)
    x = billiard.Pool(2)
    x.apply_async(f, (8, ), callback=cb)

    x.close()
    x.join()


if __name__ == "__main__":
    billiard.freeze_support()
    main()
