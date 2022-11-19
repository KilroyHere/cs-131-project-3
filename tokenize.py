from intbase import InterpreterBase, ErrorType


class Tokenizer:
  # Performs tokenization and returns the tokenized program

  def tokenize(self, line):
    """Tokenizes a line into Brewin tokens

    Args:
        line (string): A line of Brewin code

    Returns:
        tokenized_line: A toknized statement
    """
    tokens = [""]
    inQuotes = False
    for i in range(len(line)):
      char = line[i]

      if (char == " " and not inQuotes):
        if (tokens[-1] == ""):
          continue
        else:
          tokens.append("")

      # Comment case
      elif (char == "#"):
        if (inQuotes):
          tokens[-1] = tokens[-1] + char
        else:
          break

      # Quotation case
      elif (char == "\""):
        tokens[-1] = tokens[-1] + "\""
        if (not inQuotes):
          inQuotes = True
        else:
          inQuotes = False

      # Normal case
      else:
        tokens[-1] = tokens[-1] + char

    # Handling comments now equal to empty string
    if (len(tokens) > 1 and tokens[-1] == ""):
      tokens = tokens[:-1]
    return tokens