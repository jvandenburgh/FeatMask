import numpy as np
from matplotlib import cm

class tokenizer:
  def __init__(self, tokenize, encode, decode):
    self.tokenize = tokenize
    self.encode = encode
    self.decode = decode

default = tokenizer(lambda x: x.split(' '),
                    lambda x,**kwargs: x, 
                    lambda x: ' '.join(x))

def red_blue(v):
    if v>0:
      return np.array([0,0,v*255])
    else:
      return np.array([-v*255,0,0])

def jet_map(v):
    if v>0:
        return np.array(cm.jet(v)[:3])*255
    else:
        return np.array(cm.jet(0)[:3])*255

def score(a,b,c,d):
  if a>b:
    return (a-b)/(d-b)
  else:
    return (a-b)/(b-c)

class TextExplainer:
  def __init__(self, model, mask = ' ', tokenizer = default):
    self.model = model
    self.mask = mask
    self.tokenizer = tokenizer

  def replace_word(self, tokenized_text, i):
    masked_text = tokenized_text[:]
    masked_text[i] = self.mask
    encoded_text = self.tokenizer.encode(masked_text, add_special_tokens=False)
    decoded_text = self.tokenizer.decode(encoded_text)
    return decoded_text

  def get_feature_values(self, text):
    values = []
    tokenized_text = self.tokenizer.tokenize(text)
    for i in range(len(tokenized_text)):
      decoded_text = self.replace_word(tokenized_text, i)
      values.append(self.model(decoded_text))
    return values

  def explain_instance(self, text):
    tokenized_text = self.tokenizer.tokenize(text)
    model_value = self.model(text)
    values = self.get_feature_values(text)
    max_value = max(values)
    min_value = min(values)
    explanation = [score(v,model_value,min_value,max_value) for v in values]
    return explanation

  def visualize_explanation(self, text, color_function=red_blue):
    tokenized_text = self.tokenizer.tokenize(text)
    explanation = self.explain_instance(text)
    colored_text = ""
    for i in range(len(tokenized_text)):
      modified_text = ' ' + tokenized_text[i]
      modified_text = modified_text.replace(' ##', '')
      color = color_function(explanation[i])
      new_text = "\x1b[38;2;{};{};{}m{}\x1b[38;2;255;255;255m".format(int(color[0]), int(color[1]), int(color[2]), modified_text)
      colored_text = colored_text + new_text
    return print(colored_text)

class ImageExplainer:
  def __init__(self, model, mask=[255,255,255], patch=[2,2]):
    self.model = model
    self.mask = mask
    self.patch = patch

  def replace_feature(self, image, i, j):
      masked_image = np.array(image)
      for s in range(self.patch[0]):
          for t in range(self.patch[1]):
              masked_image[i+s,j+t] = self.mask
      return masked_image

  def get_feature_values(self, image):
      values = []
      for i in range(int(image.shape[0]/self.patch[0])):
          for j in range(int(image.shape[1]/self.patch[1])):
              modified_image = self.replace_feature(image, i*self.patch[0], j*self.patch[1])
              values.append(self.model(modified_image))
      return values
  
  def visualize_explanation(self, image, color_function=jet_map):
    model_value = self.model(image)
    values = self.get_feature_values(image)
    max_value = max(values)
    min_value = min(values)
    explainer_image = np.array(image)
    u = int(image.shape[0]/self.patch[0])
    v = int(image.shape[1]/self.patch[1])
    for i in range(u):
        for j in range(v):
            w = int(i*v+j)
            val = score(values[w],model_value,min_value,max_value)
            color = color_function(val)
            for s in range(self.patch[0]):
              for t in range(self.patch[1]):
                explainer_image[i*self.patch[0]+s,j*self.patch[1]+t]=color
    return explainer_image
