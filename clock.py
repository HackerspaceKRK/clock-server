#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import numpy as np
import datetime
from time import sleep

def digitMatrix(x, prev=None):
    matrices = {
        0 : np.matrix('1 1 1; 1 0 1; 1 0 1; 1 0 1; 1 1 1'),
        1 : np.matrix('0 1 0; 1 1 0; 0 1 0; 0 1 0; 1 1 1'),
        2 : np.matrix('1 1 1; 0 0 1; 1 1 1; 1 0 0; 1 1 1'),
        3 : np.matrix('1 1 1; 0 0 1; 1 1 1; 0 0 1; 1 1 1'),
        4 : np.matrix('1 0 1; 1 0 1; 1 1 1; 0 0 1; 0 0 1'),
        5 : np.matrix('1 1 1; 1 0 0; 1 1 1; 0 0 1; 1 1 1'),
        6 : np.matrix('1 1 1; 1 0 0; 1 1 1; 1 0 1; 1 1 1'),
        7 : np.matrix('1 1 1; 0 0 1; 0 1 0; 0 1 0; 1 0 0'),
        8 : np.matrix('1 1 1; 1 0 1; 1 1 1; 1 0 1; 1 1 1'),
        9 : np.matrix('1 1 1; 1 0 1; 1 1 1; 0 0 1; 1 1 1'),
        (0, 1) : np.matrix('0 1 0; 1 0 0; 0 1 1; 1 0 0; 1 1 1'),
        (1, 2) : np.matrix('0 1 0; 1 0 1; 0 1 0; 1 0 0; 1 1 1'),
        (2, 3) : np.matrix('1 1 1; 0 0 1; 1 1 1; 0 1 0; 1 1 1'),
        (3, 4) : np.matrix('1 0 1; 0 1 1; 1 1 1; 0 0 1; 0 1 1'),
        (4, 5) : np.matrix('1 0 1; 1 1 0; 1 1 1; 0 0 1; 0 1 1'),
        (5, 6) : np.matrix('1 1 1; 1 0 0; 1 1 1; 0 1 1; 1 1 1'),
        (6, 7) : np.matrix('1 1 1; 0 1 0; 0 1 0; 0 1 0; 1 1 0'),
        (7, 8) : np.matrix('1 1 1; 0 1 1; 0 1 0; 0 1 0; 1 1 0'),
        (8, 9) : np.matrix('1 1 1; 1 0 1; 1 1 1; 0 1 1; 1 1 1'),
        (9, 0) : np.matrix('1 1 1; 1 0 1; 1 0 1; 0 1 1; 1 1 1'),
        (2, 0) : np.matrix('1 1 1; 0 1 1; 1 1 1; 1 1 0; 1 1 1'),
        None : np.matrix('0 0 0 ; 0 0 0; 0 0 0; 0 0 0; 0 0 0'),
    }

    if prev is not None and x != prev:
        return matrices.get( (prev,x), matrices[None] )
    else:
        return matrices.get(x, matrices[None])

def frame_number(x, prev):
    as_string = str(x)
    prev_string = str(prev)
    return np.concatenate(
        (
            [[0]]*5,
            digitMatrix(
                None if len(as_string) == 1 else int(as_string[0]),
                None if len(prev_string) == 1 else int(prev_string[0]),
            ),
            [[0]]*5,
            digitMatrix(
                int(as_string[0]) if len(as_string) == 1 else int(as_string[1]),
                int(prev_string[0]) if len(prev_string) == 1 else int(prev_string[1]),
            ),
            [[0]]*5,
        ),
        1
    ).T

def frames_to_data(a, b, c):
    def combine(a, b):
        for i in range(0, len(a)):
            yield a[i]
            yield b[i]

    second, first = np.hsplit(
        np.flipud(
            np.concatenate(
                (
                    [[0]]*9,
                    np.fliplr(c),
                    np.fliplr(b),
                    np.fliplr(a),
                ),
                1
            )
        ),
        2
    )

    return b''.join(list(
        map(
            lambda x: np.packbits(x)[0].tobytes(),
            combine(first, second)
        )
    ))

def empty_frame():
    return np.reshape(
        np.array(
            [0]*9*5
        ),
        (9,5)
    )

client = mqtt.Client()
client.connect("localhost", 1883, 60)

prev = datetime.datetime.now()
while True:
    now = datetime.datetime.now()
    client.publish(
        "display/_all/frame",
        frames_to_data(
            frame_number(now.hour, prev.hour),
            frame_number(now.minute, prev.minute),
            frame_number(now.second, prev.second)
        )
    )
    delta = now - prev
    if prev.hour == now.hour and prev.minute == now.minute and prev.second == now.second:
        sleep(max(0.01, 0.99 - (delta.microseconds/100000)))
    else:
        sleep(0.01)
    prev = now
