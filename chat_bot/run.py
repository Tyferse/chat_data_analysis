import argparse
import os
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

from v1.src import preprocess, train
from v1.src import chat


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["preprocess", "train", "chat"], help="The mode to be execute.")
    parser.add_argument("--update", action="store_true", help="Flag when model shall be updated based on current parameters")
    args = parser.parse_args()

    if args.mode == "preprocess":
        preprocess.make_train_test()
    elif args.mode == "train":
        train.model_training(args.update)
    elif args.mode == "chat":
        chat.conversation()


if __name__ == "__main__":
    main()
