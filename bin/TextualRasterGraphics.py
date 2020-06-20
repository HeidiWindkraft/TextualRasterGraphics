#!/usr/bin/env python3

import re;

# The palette keys are characters in the ASCII table
# from 0x20 until including 0x7e.

PALETTE_OFFSET = 0x20;
MAX_PALETTE_ENTRIES = 95;
PALETTE_END = PALETTE_OFFSET + MAX_PALETTE_ENTRIES;

# Regexes
#                            (1:title)
re_title = re.compile(r'^#\s+(.*)$');
#                                    (1:key)  (2:value)
re_prop_entry = re.compile(r'\s*\-\s+([^:]+)\s*:\s*(.*)$');
#                                   (1:key)   (2:value)
re_pal_entry  = re.compile(r'\s*\-\s([.\s]):\s*(.*)$');
#
re_emptyln = re.compile(r'^\s*$');

# Helpers
def _skipempty(lines, i):
  while (i < len(lines)):
    if re_emptyln.match(lines[i]):
      i += 1;
    else:
      break;
  if (i >= len(lines)):
    raise Exception("Unexpected end of file in line " + str(i));
  return i;

class TextualRasterImage:
  __slots__ = (
    'title',
    'property_key_order',
    'property_strs',
    'palette_ascii2rgba',
    'raster_lines',
    'sloppy_palette',
    'background_color',
  );
  def __init__(self):
    self.title = "UntitledTextualRasterImage";
    self.property_key_order = [ 'width', 'height', 'color-format' ];
    self.property_strs = dict();
    self.palette_ascii2rgba = [None] * 128;
    self.raster_lines = [];
    self.sloppy_palette = False;
    self.background_color = (0,0,0,0);
  def get_width(self):
    width = 0;
    if 'width' in self.property_strs:
      width = int(self.property_strs['width']);
    else:
      for line in self.raster_lines:
        if len(line) > width:
          width = len(line);
    return width;
  def get_height(self):
    height = 0;
    if 'height' in self.property_strs:
      height = int(self.property_strs['height']);
    else:
      height = len(self.raster_lines);
    return height;
  def read_image_file(self, filename):
    from PIL import Image; # https://python-pillow.org/ (Yes, I wondered about the future of PIL)
    self.title = filename;
    im = Image.open(filename, 'r');
    im = im.convert('RGBA');
    pixel_data = list(im.getdata());
    newpix = [];
    (width, height) = im.size;
    # Collect pixels and build palette
    rgba_map = dict();
    next_palette_entry = 0;
    for rgba in pixel_data:
      pe = None; # palette entry (zero-based index)
      if rgba not in rgba_map:
        if next_palette_entry >= MAX_PALETTE_ENTRIES:
          pe = MAX_PALETTE_ENTRIES - 1;
          if not self.sloppy_palette:
            raise Exception("Cannot express palette of image \""+str(filename)
              +"\". There are more than "+MAX_PALETTE_ENTRIES+" colors");
        else:
          pe = next_palette_entry;
          next_palette_entry += 1;
          rgba_map[rgba] = pe;
      else:
        pe = rgba_map[rgba];
      newpix.append(pe);
    # Fill palette
    for (rgba, index) in rgba_map.items():
      self.palette_ascii2rgba[index + PALETTE_OFFSET] = rgba;
    # Fill raster lines
    it = 0;
    for y in range(0, height):
      line = "";
      for x in range(0, width):
        line += chr(newpix[it] + PALETTE_OFFSET);
        it += 1;
      self.raster_lines.append(line);
    # Fill property strings
    self.property_strs['width']  = str(width);
    self.property_strs['height'] = str(height);
    self.property_strs['color-format'] = "hex-rgba";
    if self.palette_ascii2rgba[ord('`')] is not None:
      self.property_strs['indented1s'] = "yes";
    # -
    return;
  def read_hex_rgba(self, value):
    r = int(value[0:2], 0x10);
    g = int(value[2:4], 0x10);
    b = int(value[4:6], 0x10);
    a = int(value[6:8], 0x10);
    return (r,g,b,a);
  def read_md_lines(self, lines):
    i = 0;
    i = _skipempty(lines, i);
    # Read title
    m = re_title.match(lines[i]);
    if not m:
      raise Exception("File incomplete at line " + str(i) + ". Cannot match title in: " + lines[i]);
    i += 1;
    self.title = m.group(1);
    # Read properties
    i = _skipempty(lines, i);
    if lines[i].rstrip() != "## properties":
      raise Exception("File incomplete at line " + str(i) + ". Cannot find properties in: " + lines[i]);
    i += 1;
    self.property_key_order = [];
    i = _skipempty(lines, i);
    while ((i < len(lines)) and not lines[i].startswith("#")):
      m = re_prop_entry.match(lines[i]);
      if not m:
        raise Exception("Unexpected property format at line " + str(i) + ": " + lines[i]);
      key = m.group(1);
      value = m.group(2);
      self.property_key_order.append(key);
      self.property_strs[key] = value;
      i = _skipempty(lines, i + 1);
      continue;
    # Read palette
    if lines[i].rstrip() != "## palette":
      raise Exception("File incomplete at line " + str(i) + ". Cannot find properties in: " + lines[i]);
    i += 1;
    i = _skipempty(lines, i);
    raw_palette = dict();
    while ((i < len(lines)) and not lines[i].startswith("#")):
      m = re_prop_entry.match(lines[i]);
      if not m:
        raise Exception("Unexpected palette entry format at line " + str(i) + ": " + lines[i]);
      key = m.group(1);
      value = m.group(2);
      raw_palette[key] = value;
      i = _skipempty(lines, i + 1);
      continue;
    # Assemble palette
    color_format = self.property_strs['color-format'];
    if color_format != 'hex-rgba':
      raise Exception("Unknown color-format: " + color_format);
    for keych in raw_palette:
      key = ord(keych);
      if (PALETTE_OFFSET > key) or (key >= PALETTE_END):
        raise Exception("Palette character is out of range (" + str(key) + "):" + keych);
      self.palette_ascii2rgba[key] = self.read_hex_rgba(raw_palette[keych]);
    if 'background-color' in self.property_strs:
      self.background_color = self.read_hex_rgba(self.property_strs['background-color']);
    # Read raster
    if lines[i].rstrip() != "## raster":
      raise Exception("File incomplete at line " + str(i) + ". Cannot find raster in: " + lines[i]);
    i += 1;
    i = _skipempty(lines, i);
    if lines[i].rstrip() != "```":
      raise Exception("File incomplete at line " + str(i) + ". Cannot find raster code in: " + lines[i]);
    i += 1;
    indented1s = (self.property_strs.get('indented1s','no') == 'yes');
    while ((i < len(lines)) and (lines[i].rstrip() != "```")):
      line = lines[i].rstrip('\r\n');
      if indented1s:
        line = line[1:];
      self.raster_lines.append(line);
      i += 1;
      continue;
    return;
  def read_md_file(self, filename):
    with open(filename, 'r') as fh:
      self.read_md_lines(fh.readlines());
    return;
  def _getrgba(self, line, x):
    rgba = self.palette_ascii2rgba[ord(line[x])];
    if rgba is None:
      if self.sloppy_palette:
        rgba = self.background_color;
      else:
        raise Exception("The following character does not correspond "
            + "to a palette entry(" + ord(line[x]) + "): " + line[x]);
    return rgba;
  def write_image_file(self, filename):
    from PIL import Image;
    width = self.get_width();
    height = self.get_height();
    linescale = int(self.property_strs.get('linescale', '1'));
    img = Image.new('RGBA', (width, height*linescale));
    # Set pixeldata
    data = [];
    for y in range(0, height):
      line = self.raster_lines[y];
      for linescaler in range(0, linescale):
        lw = width;
        ll = len(line);
        if ll < width:
          lw = ll;
        for x in range(0, lw):
          data.append(self._getrgba(line, x));
        if ll < width:
          # fill the rest with the background color.
          data.extend([self.background_color] * (width - ll));
    img.putdata(data);
    #   img = Image.new('P', (width, height));
    #   # Set palette
    #   #   palette_tuples = [];
    #   #   for pe in self.palette_ascii2rgba[PALETTE_OFFSET:PALETTE_END]:
    #   #     (r, g, b, a) = pe if pe is not None else self.background_color;
    #   #     palette_tuples.append((r, g, b, a));
    #   #   #  Fill the rest with the background color.
    #   #   (r, g, b, a) = self.background_color;
    #   #   palette_tuples.extend([(r, g, b, a)] * (256 - MAX_PALETTE_ENTRIES));
    #   #   print (palette_tuples);
    #   #   img.putpalette(palette_tuples, 'RGBA');
    #   # Set palette
    #   #   palette_bytes = bytearray();
    #   #   for pe in self.palette_ascii2rgba[PALETTE_OFFSET:PALETTE_END]:
    #   #     pe = list(pe if pe is not None else self.background_color);
    #   #     palette_bytes.extend(pe);
    #   #   #  Fill the rest with the background color.
    #   #   palette_bytes.extend(list(self.background_color) * (256 - MAX_PALETTE_ENTRIES));
    #   #   img.putpalette(palette_bytes, 'RGBA');
    #   # Set palette
    #   palette_bytes = bytearray();
    #   for pe in self.palette_ascii2rgba[PALETTE_OFFSET:PALETTE_END]:
    #     pe = list(pe if pe is not None else self.background_color);
    #     palette_bytes.extend(pe[0:3]);
    #   #  Fill the rest with the background color.
    #   palette_bytes.extend(list(self.background_color)[0:3] * (256 - MAX_PALETTE_ENTRIES));
    #   img.putpalette(palette_bytes, 'RGB');
    #   # Set pixeldata
    #   data = [];
    #   for y in range(0, height):
    #     line = self.raster_lines[y];
    #     lw = width;
    #     ll = len(line);
    #     if ll < width:
    #       lw = ll;
    #     for x in range(0, lw):
    #       data.append(ord(line[x]) - PALETTE_OFFSET);
    #     if ll < width:
    #       # fill the rest with the background color.
    #       data.extend([MAX_PALETTE_ENTRIES] * (width - ll));
    #   img.putdata(data);
    #   # Set alpha, because something seems to be wrong with putpalette.
    # Write to file
    img.save(filename);
    return;
  def write_md_lines(self):
    lines = [
      "# " + self.title,
      "",
      "## properties",
      ""
    ];
    remaining_keys = set(self.property_strs.keys());
    for key in self.property_key_order:
      if key in remaining_keys:
        remaining_keys.remove(key);
        value = self.property_strs[key];
        lines.append("- " + key + ": " + value);
    for key in sorted(list(remaining_keys)):
      value = self.property_strs[key];
      lines.append("- " + key + ": " + value);
    lines.extend([
      "",
      "## palette",
      "",
    ]);
    for i in range(PALETTE_OFFSET, PALETTE_OFFSET + MAX_PALETTE_ENTRIES):
      key = chr(i);
      valuet = self.palette_ascii2rgba[i];
      if valuet is not None:
        (r,g,b,a) = valuet;
        value = "{:02x}{:02x}{:02x}{:02x}".format(r,g,b,a);
        lines.append("- " + key + ": " + value);
    lines.extend([
      "",
      "## raster",
      "",
      "```",
    ]);
    indented1s = (self.property_strs.get('indented1s','no') == 'yes');
    if indented1s:
      lines.extend([' '+l for l in self.raster_lines]);
    else:
      lines.extend(self.raster_lines);
    lines.extend([
      "```",
      "",
    ]);
    return lines;
  def write_md_str(self):
    lines = self.write_md_lines();
    return '\n'.join(lines);
  def write_md_file(self, filename):
    with open(filename, 'w') as fh:
      fh.write(self.write_md_str());
    return;
  def _svgrectstr(self, rgba, x, y, width, height):
    (r, g, b, a) = rgba;
    return ('  <rect x="'+str(x)
              +'" y="'+str(y)
              +'" width="'+str(width)
              +'" height="'+str(height)
              +'" style="fill:rgba('+str(r)+','+str(g)+','+str(b)+','+str(a)+')" />');
  def write_svg_lines(self):
    width = self.get_width();
    height = self.get_height();
    pixw = int(self.property_strs.get('svg-pixel-width', '1'));
    pixh = int(self.property_strs.get('svg-pixel-height', '1'));
    linescale = int(self.property_strs.get('linescale', '1'));
    pixh *= linescale;
    lines = [
      '<svg width="' + str(width*pixw) + '" height="' + str(height*pixh) + '">',
      '',
    ];
    for y in range(0, height):
      line = self.raster_lines[y];
      lw = width;
      ll = len(line);
      if ll < width:
        lw = ll;
      for x in range(0, lw):
        lines.append(self._svgrectstr(self._getrgba(line, x), x*pixw, y*pixh, pixw, pixh));
      if ll < width:
        # fill the rest with the background color.
        for x in range(ll, width):
          lines.append(self._svgrectstr(self.background_color, x*pixw, y*pixh, pixw, pixh));
      lines.append('');
    lines.extend([
      "</svg>",
      ""
    ]);
    return lines;
  def write_svg_str(self):
    return '\n'.join(self.write_svg_lines());
  def write_svg_file(self, filename):
    with open(filename, 'w') as fh:
      fh.write(self.write_svg_str());
    return;


def main():
  import argparse;
  parser = argparse.ArgumentParser(description='TextualRasterImage processing');
  parser.add_argument('--txt-in', help='Textual input');
  parser.add_argument('--img-in', help='Image input');
  parser.add_argument('--txt-out', help='Textual output');
  parser.add_argument('--img-out', help='Image output');
  parser.add_argument('--svg-out', help='SVG output');
  args = parser.parse_args();
  trg = TextualRasterImage();
  if args.txt_in is not None:
    trg.read_md_file(args.txt_in);
  if args.img_in is not None:
    trg.read_image_file(args.img_in);
  if args.txt_out is not None:
    trg.write_md_file(args.txt_out);
  if args.img_out is not None:
    trg.write_image_file(args.img_out);
  if args.svg_out is not None:
    trg.write_svg_file(args.svg_out);
  return;

if __name__ == '__main__':
  main();
