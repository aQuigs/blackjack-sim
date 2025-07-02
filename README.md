# Blackjack Simulator

Tool used to simulate table games such as Blackjack and Spanish 21

## Usage

1. Create and activate the virtual environment

    ```sh
    python3 -m venv .venv
    . .venv/bin/activate
    ```

2. Install precommit hooks

    ```sh
    pre-commit install
    ```

3. Install the requirements

    ```sh
    pip install -r requirements.txt
    ```

4. Run the sim
   - note: 100,000 rounds is a low amount for a real run

    ```sh
    python -m blackjack.cli --num-rounds 100000 --parallel 8 --num-decks 6 > results.txt
    ```
