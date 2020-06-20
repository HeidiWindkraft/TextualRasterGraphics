# TextualRasterGraphics

Just something pointless.

TextualRasterGraphics allows you to describe a raster image in a textual way
that is github-markdown compatible.

## Example

File [examples/smiley.trg.md](examples/smiley.trg.md) describes a "smiley".
Use `cat examples/smiley.trg.md` to display it in ASCII format.

The following command will convert it to PNG and SVG:
```sh
bin/TextualRasterGraphics.py --txt-in examples/smiley.trg.md --img-out smiley.png
bin/TextualRasterGraphics.py --txt-in examples/smiley.trg.md --svg-out smiley.svg
```

File `smiley.svg` should look like this:
![examples/smiley.trg.md.svg](examples/smiley.trg.md.svg)


Other examples are:
  - ![examples/smiley.trg.md.svg](examples/smiley.trg.md.svg) from
    [examples/smiley.trg.md.svg](examples/smiley.trg.md.svg).
  - ![examples/indentex.trg.md.svg](examples/indentex.trg.md.svg) from
    [examples/indentex.trg.md](examples/indentex.trg.md).

## Description

TextualRasterGraphics images consist of at least three sections: `properties`, `palette` and `raster`.
They must start with a line starting with `#` which should specify the title of the image.

The properties section is started with a line containing `## properties`.
There are the following properties:
  - `color-format` (values: `hex-rgba`): Specifies how colors are described (e.g. in the palette).
    `hex-rgba` stands for red, green, blue and alpha values between 0 and 255 in hexadecimal format.
  - `background-color` (optional. color value) the color value with which raster lines shall be
    filled in case they don't have the full width.
  - `width` (optional, integer): The width of the image in pxels.
  - `height` (optional, integer): The height of the image in pxels.
  - `indented1s` (optional, `yes`/`no`): In case you want to start a raster line with three adjacent \`.

The palette section is started with a line containing `## palette`.
The palette section describes how characters in the raster are translated to a color.
Colors are specified according to the `color-format` property.
The character must be immediately followed `:`.
Legal character values are `0x20` until including `0x7e`.

Legal character values:
```
 !"#$%&'()*+,-./
0123456789:;<=>?
@ABCDEFGHIJKLMNO
PQRSTUVWXYZ[\]^_
`abcdefghijklmno
pqrstuvwxyz{|}~
```

The raster section is started with a line containing `## raster`
and a line starting with three adjacent \`.
Each line of the image is described by a line of characters
where each character describes the color of a pixel as it can found in the palette.
The raster ends with a line starting with three adjacent \`.




