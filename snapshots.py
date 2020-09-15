
import json
import os
from os import listdir
from os.path import isfile, join

# Where are we?
where_we_are = os.path.dirname(os.path.realpath(__file__))

# From wherever we are, look in /raw for files
raw_files = [f for f in listdir(where_we_are+"/raw") if isfile(join(where_we_are+"/raw", f))]

columns = {}

for raw_file in raw_files:

    with open(where_we_are+"/raw/{}".format(raw_file), "r") as f:

        # Parse out the useful bits
        for line in f:

            if "created the column" in line:
                continue

            # Disregard name only lines
            if len(line.split(" ")) == 1:
                continue

            # Now diesregard anything that DOESN'T start with a name
            if not line.startswith("@"):
                continue

            # New things added
            tokens = line.strip().split(" ")

            # Format for output
            pathfied_name = tokens[2]
            rejoined_n_pretty = " ".join([x.capitalize() for x in pathfied_name.split("-")])

            if tokens[1] == "added" and tokens[-2] == "To" and tokens[-1] == "do":
                if "To do" not in columns.keys():
                    columns.update({"To do": []})
                columns["To do"].append({rejoined_n_pretty:pathfied_name})
            else:

                # Should be a move of some kind
                relevent_bit = " ".join(tokens[3:])
                if not relevent_bit.startswith("from"):
                    raise Exception('Cannot parse, expecting "{}" to start with "from": '.format(relevent_bit))

                assert len([x for x in relevent_bit.split(" ") if x == "to"]) == 1,'Aborting, the word "to" appears twice in "{}". It\'ll mess up the parser.'.format(relevent_bit)

                is_from = relevent_bit.replace("from ", "").split("to")[0].strip()
                if is_from not in columns.keys():
                    columns[is_from] = []
                columns[is_from].append({rejoined_n_pretty:pathfied_name})

                going_to = relevent_bit.replace("from ", "").split("to")[1].strip()
                if going_to not in columns.keys():
                    columns[going_to] = []
                columns[going_to].append({rejoined_n_pretty:pathfied_name})

    # coolio, dump it out as json for later
    with open(where_we_are+"/snapshots/{}.json".format(raw_file[:-4]), "w") as f:
        json.dump(columns, f)

    # lastly, make a parsed version (less human readable, but great for iterating in a template)
    with open(where_we_are+"/parsed/{}.json".format(raw_file[:-4]), "w") as f:

        # TODO - how do we create this dynamically but keep order?
        headers = (
            "To do", 
            "Stage 1 Transform Spec",
            "Stage 1 Transform",
            "Stage 2 Alignment Spec", 
            "Stage 2 Transform - Alignment",
            "To fix",
            "On PMD with Issues",
            "To Review"
        )

        for header in headers:
            if header not in columns.keys():
                columns[header] = []


        # Get the unique things what we've added
        unique_items = []
        for value in columns.values():
            for value_entry in value:
                for k in value_entry.keys():
                    unique_items.append(k)
        unique_items = set(unique_items)

        final = []
        column_entry_found = {}

        rows = []
        for column in headers:

            for i, pipeline in enumerate(unique_items):
                if len(rows) <= i:
                    rows.append(())
                items_in_column = [list(x.keys())[0] for x in columns[column]]
                if pipeline in items_in_column:
                    l_from_t = list(rows[i])
                    l_from_t.append({pipeline: pipeline})
                    rows[i] = tuple(l_from_t)
                else:
                    l_from_t = list(rows[i])
                    l_from_t.append("")
                    rows[i] = tuple(l_from_t)


        """
        for pipeline in unique_items:
            row = []
            for column in columns.keys():
                if column not in column_entry_found.keys():
                    column_entry_found[column] = []
                found = False

                for isItem in columns[column]:
                    if pipeline == list(isItem.keys())[0]:
                        found = True
                        if pipeline not in column_entry_found[column]:
                            column_entry_found[column].append(pipeline)
                            row.append({list(isItem.keys())[0].strip():list(isItem.values())[0].strip()})
                        continue

                if found:
                    continue
                else:
                    row.append("")
            final.append(row)
        """

        for_flask = {
            "header": headers,
            "rows": rows
        }


        for row in for_flask["rows"]:
            print(len(row))

        json.dump(for_flask, f)    

