#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import numpy as np
import datetime
from time import sleep

def digitMatrix(x):
    return {
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
        42 : np.matrix('0 0 0 ; 0 0 0; 0 0 0; 0 0 0; 0 0 0'),
    }.get(x, np.matrix('0 0 0 ; 0 0 0; 0 0 0; 0 0 0; 0 0 0'))

def frame_number(x):
    as_string = str(x)
    return np.concatenate(
        (
            [[0]]*5,
            digitMatrix(
                0 if len(as_string) == 1 else int(as_string[0])
            ),
            [[0]]*5,
            digitMatrix(
                int(as_string[0]) if len(as_string) == 1 else int(as_string[1])
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

while True:
    now = datetime.datetime.now()
    client.publish(
        "display/_all/frame",
        frames_to_data(
            frame_number(now.hour),
            frame_number(now.minute),
            frame_number(now.second)
        )
    )
    sleep(1)
