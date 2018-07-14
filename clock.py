#!/usr/bin/env python3
import paho.mqtt.client as mqtt
import numpy as np
import datetime
from time import sleep
import functools

matrices = {
    0: np.matrix('1 1 1; 1 0 1; 1 0 1; 1 0 1; 1 1 1'),
    1: np.matrix('0 1 0; 1 1 0; 0 1 0; 0 1 0; 1 1 1'),
    2: np.matrix('1 1 1; 0 0 1; 1 1 1; 1 0 0; 1 1 1'),
    3: np.matrix('1 1 1; 0 0 1; 1 1 1; 0 0 1; 1 1 1'),
    4: np.matrix('1 0 1; 1 0 1; 1 1 1; 0 0 1; 0 0 1'),
    5: np.matrix('1 1 1; 1 0 0; 1 1 1; 0 0 1; 1 1 1'),
    6: np.matrix('1 1 1; 1 0 0; 1 1 1; 1 0 1; 1 1 1'),
    7: np.matrix('1 1 1; 0 0 1; 0 1 0; 0 1 0; 1 0 0'),
    8: np.matrix('1 1 1; 1 0 1; 1 1 1; 1 0 1; 1 1 1'),
    9: np.matrix('1 1 1; 1 0 1; 1 1 1; 0 0 1; 1 1 1'),
    (0, 1): np.matrix('0 1 0; 1 0 0; 0 1 1; 1 0 0; 1 1 1'),
    (1, 2): np.matrix('0 1 0; 1 0 1; 0 1 0; 1 0 0; 1 1 1'),
    (2, 3): np.matrix('1 1 1; 0 0 1; 1 1 1; 0 1 0; 1 1 1'),
    (3, 4): np.matrix('1 0 1; 0 1 1; 1 1 1; 0 0 1; 0 1 1'),
    (4, 5): np.matrix('1 0 1; 1 1 0; 1 1 1; 0 0 1; 0 1 1'),
    (5, 6): np.matrix('1 1 1; 1 0 0; 1 1 1; 0 1 1; 1 1 1'),
    (6, 7): np.matrix('1 1 1; 0 1 0; 0 1 0; 0 1 0; 1 1 0'),
    (7, 8): np.matrix('1 1 1; 0 1 1; 0 1 0; 0 1 0; 1 1 0'),
    (8, 9): np.matrix('1 1 1; 1 0 1; 1 1 1; 0 1 1; 1 1 1'),
    (9, 0): np.matrix('1 1 1; 1 0 1; 1 0 1; 0 1 1; 1 1 1'),
    (2, 0): np.matrix('1 1 1; 0 1 1; 1 1 1; 1 1 0; 1 1 1'),
    (5, 0): np.matrix('1 1 1; 1 1 0; 1 1 1; 0 1 1; 1 1 1'),
    None: np.matrix('0 0 0 ; 0 0 0; 0 0 0; 0 0 0; 0 0 0'),
}
frame_spacer = [[0]] * 9
char_spacer = [[0]] * 5
empty_frame = np.reshape(
    np.array(
        [0] * 9 * 5
    ),
    (9, 5)
)


def digit_matrix(previous_digit, current_digit):
    if current_digit != previous_digit:
        return matrices.get((previous_digit, current_digit), matrices[None])
    else:
        return matrices.get(current_digit, matrices[None])


@functools.lru_cache(maxsize=128, typed=False)
def frame_number(previous_number, current_number):
    current_string = str(current_number)
    previous_string = str(previous_number)

    current_length = len(current_string)
    previous_length = len(previous_string)

    return np.concatenate(
        (
            char_spacer,
            digit_matrix(
                0 if previous_length == 1 else int(previous_string[0]),
                0 if current_length == 1 else int(current_string[0])
            ),
            char_spacer,
            digit_matrix(
                int(previous_string[0]) if previous_length == 1 else int(previous_string[1]),
                int(current_string[0]) if current_length == 1 else int(current_string[1])
            ),
            char_spacer,
        ),
        1
    ).T


def combine(a, b):
    for i in range(0, len(a)):
        yield a[i]
        yield b[i]


def frames_to_data(a, b, c):
    second, first = np.hsplit(
        np.flipud(
            np.concatenate(
                (
                    frame_spacer,
                    np.fliplr(c),
                    np.fliplr(b),
                    np.fliplr(a),
                ),
                1
            )
        ),
        2
    )

    return b''.join(
        list(
            map(
                lambda x: np.packbits(x)[0].tobytes(),
                combine(first, second)
            )
        )
    )


if __name__ == '__main__':
    client = mqtt.Client()
    client.connect("localhost", 1883, 60)

    prev = datetime.datetime.now()
    while True:
        now = datetime.datetime.now()
        client.publish(
            "display/_all/frame",
            frames_to_data(
                frame_number(prev.hour, now.hour),
                frame_number(prev.minute, now.minute),
                frame_number(prev.second, now.second)
            )
        )
        delta = now - prev
        if prev.hour == now.hour and prev.minute == now.minute and prev.second == now.second:
            sleep(max(0.01, 0.99 - (delta.microseconds / 100000)))
        else:
            sleep(0.01)
        prev = now
