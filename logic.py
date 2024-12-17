import math
import json
from mido import MidiFile, MidiTrack, Message

grammar = {
    'Start': [['Pattern', 'Sequence']],
    'Sequence': [
        ['NewColumn', 'Pattern', 'Sequence'],   # Pattern generator after NewColumn so at least 1 pattern per row can be enforced
        ['Pattern', 'Sequence'],
        []                                                          # Empty Production for termination
    ],
    'Pattern': [
        ['SingleNote'],
        ['DoubleNote'],
        ['TripleNote'],
        ['QuadNote'],
        ['QuintNote']
    ],

    'SingleNote': {
        '0a': [0, 0, 0, 0, 0],
        '0b': [1, 0, 0, 0, 0],
        '1b': [0, 1, 0, 0, 0],
        '2b': [0, 0, 1, 0, 0],
        '3b': [0, 0, 0, 1, 0],
        '4b': [0, 0, 0, 0, 1],
    },
    'DoubleNote': {
        '0c': [1, 1, 0, 0, 0],
        '1c': [1, 0, 1, 0, 0],
        '2c': [1, 0, 0, 1, 0],
        '3c': [1, 0, 0, 0, 1],
        '4c': [0, 1, 1, 0, 0],
        '5c': [0, 1, 0, 1, 0],
        '6c': [0, 1, 0, 0, 1],
        '7c': [0, 0, 1, 1, 0],
        '8c': [0, 0, 1, 0, 1],
        '9c': [0, 0, 0, 1, 1],
    },
    'TripleNote': {
        '0d': [1, 1, 1, 0, 0],
        '1d': [1, 1, 0, 1, 0],
        '2d': [1, 1, 0, 0, 1],
        '3d': [1, 0, 1, 1, 0],
        '4d': [1, 0, 1, 0, 1],
        '5d': [1, 0, 0, 1, 1],
        '6d': [0, 1, 1, 1, 0],
        '7d': [0, 1, 1, 0, 1],
        '8d': [0, 1, 0, 1, 1],
        '9d': [0, 0, 1, 1, 1],
    },
    'QuadNote': {
        '0e': [1, 1, 1, 1, 0],
        '1e': [1, 1, 1, 0, 1],
        '2e': [1, 1, 0, 1, 1],
        '3e': [1, 0, 1, 1, 1],
        '4e': [0, 1, 1, 1, 1],
    },
    'QuintNote': {
        '0f': [1, 1, 1, 1, 1],
    },
    'NewColumn': {
        '9p': 'newline',
    },
}


def get_keys(dictionary):
    return [k for k in dictionary.keys()]


token_list = []
token_max_length = 2
for item in grammar.values():
    if isinstance(item, dict):
        token_list += get_keys(item)


def tokenize(text):
    global token_list, token_max_length
    tokens = []
    start = 0
    end = 1
    while end <= len(text):
        token = text[start:end]
        if len(token) > token_max_length:
            raise ValueError("Failed to tokenize")
        if token in token_list:
            tokens.append(token)
            start = end
        end += 1
    if end - start > 1:
        raise ValueError("Failed to tokenize")
    return tokens


def parse_rule(rule_name, tokens, index):
    print(f"Parsing rule: {rule_name}, Tokens: {tokens[index:]}, Index: {index}")

    # Check if the rule exists in the grammar
    if rule_name not in grammar:
        raise KeyError(f"Grammar rule '{rule_name}' not found.")

    rule_def = grammar[rule_name]

    if isinstance(rule_def, dict):
        # Terminal symbol
        if index < len(tokens) and tokens[index] in rule_def:
            token_value = rule_def[tokens[index]]
            print(f"Matched terminal: {tokens[index]} to rule: {rule_name}")
            return {'type': rule_name, 'token': tokens[index], 'value': token_value, 'index': index + 1}
        else:
            print(f"Failed to match terminal: {tokens[index] if index < len(tokens) else 'EOF'} to rule: {rule_name}")
            return None
    elif isinstance(rule_def, list):
        # Non-terminal symbol
        for production in rule_def:
            print(f"Trying production: {production} for rule: {rule_name}")
            current_index = index
            parsed_elements = []

            if not production:
                # Empty production
                print(f"Matched empty production for rule: {rule_name}")
                return {'type': rule_name, 'elements': [], 'index': current_index}

            for symbol in production:
                print(f"Processing symbol: {symbol}")

                result = parse_rule(symbol, tokens, current_index)
                if result is None:
                    print(f"Failed to match symbol: {symbol}, Tokens: {tokens[current_index:]}, Index: {current_index}")
                    break
                parsed_elements.append(result)
                current_index = result['index']
            else:
                # Successfully matched the rule
                print(f"Matched rule: {rule_name} -> {production}")
                return {'type': rule_name, 'elements': parsed_elements, 'index': current_index}
        # Failed to match any production
        print(f"Failed to parse rule: {rule_name}, Tokens: {tokens[index:]}, Index: {index}")
        return None
    else:
        raise ValueError(f"Invalid rule definition for '{rule_name}'.")


def parse_Start(tokens):
    result = parse_rule('Start', tokens, 0)
    if result is not None and result['index'] == len(tokens):
        return result
    else:
        raise ValueError("Error: Unable to parse the input text according to the grammar.")


def process_parse_tree(parse_tree, track, logger=None):
    patterns = []
    current_section = []
    all_sections = []
    total_skips = 0

    def extract_patterns(node):
        if node['type'] in ['SingleNote', 'DoubleNote', 'TripleNote', 'QuadNote', 'QuintNote']:
            patterns.append(node['value'])
        elif node['type'] == 'NewColumn':
            patterns.append('newline')
        elif 'elements' in node:
            for child in node['elements']:
                extract_patterns(child)

    extract_patterns(parse_tree)

    for p in patterns:
        if p == 'newline':
            if current_section:
                all_sections.append(current_section)
                current_section = []
        else:
            current_section.append(p)

    if current_section:
        all_sections.append(current_section)

    # Process each section
    for section in all_sections:
        if logger:
            logger(f"Section: {section}")
        flipped_section = [list(row) for row in zip(*section)]
        if logger:
            logger(f"Flipped Section: {flipped_section}")

        starting_pitch = math.ceil(60 + len(section) / 2)
        for column in flipped_section:
            current_pitch = starting_pitch
            switch1, switch2 = True, True
            empty_switch = True
            for note in column:
                if note == 1:
                    empty_switch = False
                    if switch1:
                        track.append(Message('note_on', note=current_pitch, velocity=64, time=(total_skips * 100)))
                        total_skips = 0
                        switch1 = False
                    else:
                        track.append(Message('note_on', note=current_pitch, velocity=64, time=0))
                current_pitch -= 1

            current_pitch = starting_pitch
            for note in column:
                if note == 1:
                    if switch2:
                        track.append(Message('note_off', note=current_pitch, velocity=64, time=100))
                        switch2 = False
                    else:
                        track.append(Message('note_off', note=current_pitch, velocity=64, time=0))
                current_pitch -= 1

            if empty_switch:
                total_skips += 1


def text_to_midi2(text, output_file="result_FIX.mid", logger=None):
    try:
        tokens = tokenize(text)
        parse_tree = parse_Start(tokens)

        # Print the parse tree and save to a file
        parse_tree_str = json.dumps(parse_tree, indent=2)
        print(parse_tree_str)
        with open('parse_tree.txt', 'w') as f:
            f.write(parse_tree_str)

        # MIDI File Setup
        mid = MidiFile()
        track = MidiTrack()
        mid.tracks.append(track)
        # Process the parse tree to generate MIDI
        process_parse_tree(parse_tree, track, logger)
        # Save the MIDI file with the specified name
        mid.save(output_file)
        if logger:
            logger(f"MIDI file generated successfully as '{output_file}'.")
    except ValueError as ve:
        if logger:
            logger(str(ve), is_error=True)
        else:
            print(f"\033[91m{ve}\033[0m")  # Print error in red text
    except Exception as e:
        if logger:
            logger(f"An unexpected error occurred: {e}", is_error=True)
        else:
            print(f"\033[91mAn unexpected error occurred: {e}\033[0m")  # Print unexpected errors in red text


def text_to_array(text, logger=None):
    try:
        tokens = tokenize(text)
        parse_tree = parse_Start(tokens)

        all_sections = []
        current_section = [[] for _ in range(5)]

        # recursive function to convert parse tree to result
        def extract_patterns(node, patterns=None):
            if patterns is None:
                patterns = []

            if node['type'] in ['SingleNote', 'DoubleNote', 'TripleNote', 'QuadNote', 'QuintNote']:
                patterns.append(node['value'])
            elif node['type'] == 'NewColumn':
                patterns.append('newline')
            elif 'elements' in node:
                for child in node['elements']:
                    extract_patterns(child, patterns)
            return patterns

        result = extract_patterns(parse_tree)

        for item in result:
            if item == 'newline':
                all_sections += current_section
                current_section = [[] for _ in range(5)]
            else:
                for i in range(5):
                    current_section[i].append(item[i])
        if current_section:
            all_sections += current_section
        return all_sections
    except ValueError as ve:
        raise ve
    except Exception as e:
        raise f"An unexpected error occurred: {e}"


# # Example usage:
# # Test Case 1: Single Token
# print("=== Test Case 1: simple ===")
# text = "1d"
#
# # Tokenize the input
# tokens = tokenize(text)
#
# # Parse the tokens starting from the 'Start' rule
# parse_tree = parse_Start(tokens)
#
# # Print the resulting parse tree
# print(json.dumps(parse_tree, indent=2))
#
# # Process the parse tree and generate a MIDI file
# text_to_midi2(text, output_file="result_FIX_dynamic_single.mid")
#
# # Test Case 2: Two Tokens
# print("\n=== Test Case 2: Two Tokens 'YINYANG' ===")
# text = "0a9c9d4e4e0f0f0f0f0f0e6d6d9d9c0a9p0f0f0f5d5d0f0f0f0e0a0a9c9c0a0c0f9p0b0d0e2d2d0c0b0a0a0a0a4b9c7c4c0b9p0a0a0a0a0a0b0b0b0b0b0b0a0a0a0a0a"
#
# # Tokenize the input
# tokens = tokenize(text)
#
# # Parse the tokens starting from the 'Start' rule
# parse_tree = parse_Start(tokens)
#
# # Print the resulting parse tree
# print(json.dumps(parse_tree, indent=2))
#
# # Process the parse tree and generate a MIDI file
# text_to_midi2(text, output_file="result_FIX_YINYANG.mid")
#
# # Test Case 3: Tokens with NewColumn
# print("\n=== Test Case 3: SANS ===")
# text = "0a0a0a4b3b2b1b1b0b0b0b3c5d5d5d6c1b2b2b1b1b6c1b2b2b3b4b0a0a0a9p0a9d0c0a0a0a0a0a0a0a4e0f0f0d0d0f4e0a9c1b4c2e5c7c9c0a0a0c9d0a9p0f0a0a0a0a0a0a0a0a0a0c0d0d0d0d0c0c3c4b4b0a0a0f2b2b0d9d0a0a0f9p0f0a0a0a0a0a0a0a0a0a0a4b4b4b4b0c0c0d0d0d0a0a0f3c3c3c0f0a0a0f9p0c9d0a0a0a0a0a0a0a0a0f0f0f2d2d0f0f1b7c0a0a9c1e8c7c4c0b0a9d0c9p0a0a0c2b3b4b0a0a0a0a0b0d0e0e0e0d0b4b4b0b0c0d0b4b4b3b2b0c0a0a9p0a0a0a0a0a0a0b0b1b1b1b1b1b1b1b0b0b0a0a0b0b0b0b0a0a0a0a0a0a0a"
#
# # Tokenize the input
# tokens = tokenize(text)
#
# # Parse the tokens starting from the 'Start' rule
# parse_tree = parse_Start(tokens)
#
# # Print the resulting parse tree
# print(json.dumps(parse_tree, indent=2))
#
# # Process the parse tree and generate a MIDI file
# text_to_midi2(text, output_file="result_FIX_SANS.mid")
