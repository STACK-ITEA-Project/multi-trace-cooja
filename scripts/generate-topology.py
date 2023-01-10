#!/usr/bin/env python3

import argparse
from itertools import product
import math
import os
import random
import sys
from coojasim import Cooja, UDGMRadioMedium
import re

def get_distance(mote, x, y):
    dx = abs(x - mote.position.x)
    dy = abs(y - mote.position.y)
    return math.sqrt(dx ** 2 + dy ** 2)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('-i', dest='input', required=True, nargs='+')
    p.add_argument('-o', dest='output', required=True)
    p.add_argument('-c', dest='count', type=int, default=1)
    p.add_argument('--seed', dest='seed_policy', choices=['r', 'g', 'f'], default='r',
                   help="Set seed policy. 'r' for random seed, 'g' for generated seed, 'f' for fixed seed")
    p.add_argument('--topology', dest='topology', default=None)
    p.add_argument('--min-distance', dest='min_distance', type=int, default=0)
    p.add_argument('--tx-ratio', dest='tx_ratio', type=float, default=[1.0], nargs='+',
                   help="Transmission ratio of network. Values will be rounded up to 2 digits.")
    p.add_argument('--rx-ratio', dest='rx_ratio', type=float, default=[1.0], nargs='+',
                   help="Receive ratio of network. Values will be rounded up to 2 digits.")
    try:
        args = p.parse_args(sys.argv[1:])
    except Exception as e:
        sys.exit(f"Illegal arguments: {str(e)}")

    for input_path in args.input:
        if min(args.tx_ratio) < 0.0 or max(args.tx_ratio) > 1.0:
            print(f'Tx ratio must be between 0.0 and 1.0 ({args.tx_ratio} was given)')
            sys.exit("Invalid Tx ratio")
        if min(args.rx_ratio) < 0.0 or max(args.rx_ratio) > 1.0:
            print(f'Rx ratio must be between 0.0 and 1.0 ({args.rx_ratio} was given)')
            sys.exit("Invalid Rx ratio")

        args.tx_ratio = [round(t, 2) for t in args.tx_ratio]
        args.rx_ratio = [round(r, 2) for r in args.rx_ratio]
        output_dir = os.path.dirname(args.output) if os.path.splitext(args.output) != '' else args.output
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        c = Cooja(input_path)

        if args.seed_policy == 'g':
            # Tell Cooja to generate a new random seed each time simulation runs
            c.sim.random_seed.set_generated()

        radio_medium = c.sim.radio_medium
        tx_range = radio_medium.transmitting_range if isinstance(radio_medium, UDGMRadioMedium) else 50.0
        max_range = tx_range * len(c.sim.get_motes())
        print(f"Using tx range {tx_range} meters with max multihop range of {max_range} meters.")

        if args.min_distance > 0 and args.min_distance >= tx_range:
            print('Minimal distance between nodes is too large for communication range')
            sys.exit("Too large minimal distance")

        promote_multihop = True
        if args.topology == 'spread':
            promote_multihop = False
        RSs = [
            "123456",
            "654321",
            "123123",
            "456456",
            "102030",
            "123523",
            "734563",
            "934562",
            "261032",
            "589012",
        ]

        for i in range(0, args.count):
            x = y = sx = sy = 0
            motes = []

            if args.seed_policy == 'r':
                # Set a new random seed for each new simulation
                c.sim.random_seed.set_seed(random.randint(0, 0x7fffffff))
            elif args.seed_policy == 'f':
                c.sim.random_seed.set_seed(RSs[i])
                print('i', i)

            for m in c.sim.get_motes():
                if not motes:
                    # Simply use first mote with its original position
                    motes.append(m)
                    sx = m.position.x
                    sy = m.position.y
                    print(f"position for first mote {m.mote_id:>5} is {sx:20.15f},{sy:20.15f}")
                else:
                    done = False
                    while not done:
                        if promote_multihop:
                            x = random.uniform(sx - max_range / 2 + 1, sx + max_range / 2 - 1)
                            y = random.uniform(sy + 1, sy + max_range - 1)
                        else:
                            x = random.uniform(sx - max_range + 1, sx + max_range - 1)
                            y = random.uniform(sy - max_range + 1, sy + max_range - 1)
                        for p in motes:
                            distance = get_distance(p, x, y)
                            if distance < tx_range:
                                done = True
                                break
                        if done and args.min_distance > 0:
                            for p in motes:
                                distance = get_distance(p, x, y)
                                if distance < args.min_distance:
                                    done = False
                                    break

                    m.position.x = x
                    m.position.y = y
                    motes.append(m)
                    print(f"setting position for mote {m.mote_id:>3} to {m.position.x:20.15f},{m.position.y:20.15f}")

            for t_rat, r_rat in product(args.tx_ratio, args.rx_ratio):
                radio_medium.success_ratio_tx = t_rat
                radio_medium.success_ratio_rx = r_rat

                output_file = os.path.splitext(args.output)[0]
                
                _output_file = re.sub(r'rpl-udp-base-10-attack',f'{output_file}',os.path.split(input_path)[1])
                if len(args.rx_ratio) != 1 or len(args.tx_ratio) != 1:
                    output_file += f'-tx{t_rat:.2f}-rx{r_rat:.2f}'
                    _output_file = re.sub(r'-base',f'-tx{t_rat:.2f}-rx{r_rat:.2f}',_output_file)
                if args.count > 1:
                    output_file += f'-{i + 1:05}'
                    _output_file = re.sub(r'.csc',f'-{i + 1:05}.csc',_output_file)
                if args.topology == 'spread':
                    _output_file = re.sub(r'.csc',f'-spread.csc',_output_file)
                output_file += '.csc'
                print(f'Generated {output_file}')
                print(f'Test {_output_file}')
                # print('os.path.join(conopts.output, os.path.split(input_path)[1])', os.path.join(args.output, os.path.split(input_path)[1]))
                c.save(_output_file)


if __name__ == '__main__':
    main()
