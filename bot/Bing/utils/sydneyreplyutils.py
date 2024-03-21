import re
# 拼接字符串，去除首尾重复部分
def concat_reply(former_str: str, latter_str: str) -> str:
    former_str = former_str.strip()
    latter_str = latter_str.strip()
    min_length = min(len(former_str), len(latter_str))
    for i in range(min_length, 0, -1):
        if former_str[-i:] == latter_str[:i]:
            return former_str + latter_str[i:]
    return former_str + latter_str

def remove_extra_format(reply: str) -> str:
    pattern = r'回复[^：]*：(.*)'
    result = re.search(pattern, reply, re.S)
    if result is None:
        return reply
    result = result.group(1).strip()
    if result.startswith("“") and result.endswith("”"):
        result = result[1:-1]
    return result

def except_chinese_char(string):
    import unicodedata
    # loop through each character in the string
    for char in string:
        # get the general category of the character
        category = unicodedata.category(char)
        # check if the category is Lo or Nl
        if category == 'Lo' or category == 'Nl':
        # return True if a Chinese character is found
            return False
    # return False if no Chinese character is found
    return True

def cut_botstatement(data, text_to_cut):
    """Cuts the specified text from each dictionary in the given list.

    Args:
        data: A list of dictionaries.
        text_to_cut: The text to cut from each dictionary.

    Returns:
        A new list of dictionaries with the specified text removed.
    """

    pattern = re.compile(text_to_cut)
    return [{key: re.sub(pattern, "", value) for key, value in item.items()} for item in data]

def detect_chinese_char_pair(context, threshold=5):
  """
  Detects pairs of consecutive Chinese characters that reach the threshold frequency.

  Args:
      context: The text string to analyze.
      threshold: The minimum frequency for a pair to be considered (default 5).

  Returns:
      A tuple containing:
          - True if at least one pair meets the threshold, False otherwise.
          - A list of pairs exceeding the threshold (empty if none found).
  """

  # Create a dictionary to store the frequency of each pair.
  freq = {}

  # Loop through the context with a sliding window of size 2.
  for i in range(len(context) - 1):
    pair = context[i:i+2]

    # Check if both characters are Chinese characters.
    if '\u4e00' <= pair[0] <= '\u9fff' and '\u4e00' <= pair[1] <= '\u9fff':
      # Increment the frequency of the pair or set it to 1 if not seen before.
      freq[pair] = freq.get(pair, 0) + 1

  # Find all pairs exceeding the threshold.
  exceeding_pairs = [pair for pair, count in freq.items() if count >= threshold]

  # Return results based on findings.
  if exceeding_pairs:
    return True, exceeding_pairs
  else:
    return False, []

def clip_message(text):
    if len(text) <= 10:
        return text

    if is_chinese(text):
        return text[:10]
    else:
        return text[:10]

def is_chinese(text):
    for char in text:
        if '\u4e00' <= char <= '\u9fff':
            return True
    return False

def split_sentences(text, split_punctuation):
  """Splits a text into sentences based on the provided punctuation marks.

  Args:
    text: The text to split.
    split_punctuation: A list of punctuation marks to split on.

  Returns:
    A list of sentences.
  """
  sentences = []
  start = 0
  for i, char in enumerate(text):
    if char in split_punctuation:
      sentences.append(text[start:i+1])
      start = i + 1
  sentences.append(text[start:])
  return sentences