import csv

# Input and output file names
input_file = 'widespread_panic_shows_test.csv'
output_file = 'structured_shows.csv'

# Parse the raw CSV and restructure it
def parse_shows(input_file, output_file):
    with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        # Write the header row
        writer.writerow(['Date', 'Location', 'Setlist'])

        date = None
        location = None
        setlist = []

        for line in infile:
            line = line.strip()
            if line.startswith('date:'):
                # If we already have a previous show, write it to the CSV
                if date and location and setlist:
                    writer.writerow([date, location, ', '.join(setlist)])
                # Start a new show entry
                date = line.replace('date: ', '')
                location = None
                setlist = []
            elif line.startswith('location:'):
                location = line.replace('location: ', '')
            elif line.startswith('setlist:'):
                continue  # We skip the 'setlist:' line
            elif line:  # Non-empty line (a song)
                setlist.append(line)

        # Write the last show to the CSV
        if date and location and setlist:
            writer.writerow([date, location, ', '.join(setlist)])

# Call the function to parse and convert the file
parse_shows(input_file, output_file)
print(f"Structured CSV saved to {output_file}")
