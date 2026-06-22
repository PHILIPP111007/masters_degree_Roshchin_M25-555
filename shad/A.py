import sys


def to_secs(t):
    hours, mins, secs = map(int, t.split(":"))
    return hours * 3600 + mins * 60 + secs


def main():
    M_orders = int(input())
    data = []
    for i in range(M_orders):
        d = input()
        data.append(d)

    if not data:
        return
    orders = []
    for i in range(M_orders):
        item = data[i].strip().split()
        START = to_secs(item[0])
        FINISH = to_secs(item[1])
        orders.append((START, FINISH))

    orders.sort(key=lambda x: x[0])
    available_list = []

    for start, finish in orders:
        assigned = False
        for i in range(len(available_list)):
            if available_list[i] <= start:
                available_list[i] = finish
                assigned = True
                break
        if not assigned:
            available_list.append(finish)

    print(len(available_list))


main()
