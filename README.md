# channel4

Analog broadcast television straight out of an ESP8266 pin, set up for black and white PAL TVs.

> ## This is cnlohr's work
>
> channel4 is a fork of **[cnlohr/channel3](https://github.com/cnlohr/channel3)** by Charles Lohr.
> The idea, the RF trick, the firmware, the 3D engine and the web interface are all his, and they are great.
> PAL line timing was also already in channel3, contributed there.
>
> This fork only adapts that work so it gives a solid picture on European black and white PAL sets, adds a few options around that, and explains how to build and flash it on a current Mac or Linux machine.
> The changes in this fork were made with the help of an AI coding assistant.
>
> If you have an NTSC TV, or you want color, use the original.

Solder a wire to the RX pin, flash the board, tune an old TV to channel E4 and watch a 3D demo that an ESP8266 is transmitting by toggling one pin.

## What is different from channel3

- **It broadcasts on European channel E4** (62.5 MHz) instead of US channel 3 (61.25 MHz), hence the name.
- **Black and white mode.** `MONOCHROME` leaves out all NTSC color information. The colors become clean shades of gray instead of hatching.
- **Optional bright border** for TVs that show dark screens as gray.
- **Text from Home Assistant.** A text screen that you fill over WiFi, with a ready-made Home Assistant package.
- **Recipes from Mealie.** A second package shows the ingredients and the steps of a [Mealie](https://mealie.io) recipe, one step per screen, see [Recipes from Mealie](#recipes-from-mealie).
- **It stays on your WiFi.** channel3 switches back to its own access point at every start. This fork does not.
- **A silent start.** With `START_SILENT` the TV signal only starts when something asks for a screen, and a command stops it again, see [Signal only when needed](#signal-only-when-needed).
- **Updates over WiFi that check their work.** New firmware goes on over the network, is verified and only then takes over, see [Updating over WiFi](#updating-over-wifi).
- **A filter for the antenna pin.** The TV signal jams the board's own WiFi. Two small parts at the pin fix most of that, see [WiFi and the TV signal](#wifi-and-the-tv-signal).
- **PAL and black and white are switched on by default** in `user.cfg`.
- **Setup, build and flash instructions** for macOS and Linux, below.

Everything else, including the web interface and the demo screens, is channel3.

## What you need

- **An ESP8266 board with USB and 4 MB of flash.** A Wemos D1 Mini is what this was built and tested on.
- **A USB cable that carries data.** Many micro USB cables only charge. If no serial port shows up, try another cable first.
- **A piece of wire** for the antenna, 20 to 30 cm to start with. See [Antenna](#antenna).
- **A 100 ohm resistor and a 10 pF capacitor**, if you want to use WiFi while it broadcasts. See [The filter at the pin](#the-filter-at-the-pin).
- **An analog TV that receives VHF band I** (often labeled VHF-L or VL) in the B/G standard used in most of continental Europe.
- **A Mac or a Linux PC.** macOS on Apple Silicon was used for everything here, including flashing. On Linux the setup and build steps were checked on Ubuntu 24.04. Flashing from Linux was not tried, it is the same esptool command.

## Setup, build and flash

The whole thing is six steps. Steps 1 and 2 are only needed once.

### 1. Install the tools

You need `git`, `make` and `esptool` in version 4.8.1.

**macOS** (with [Homebrew](https://brew.sh))

```sh
xcode-select --install                 # git and make, skip if you have them
brew install pipx
pipx install esptool==4.8.1
pipx ensurepath                        # then open a new terminal
softwareupdate --install-rosetta       # Apple Silicon only, the compiler is an Intel program
```

On a Mac you also need the driver for the USB serial chip on the board. The Wemos D1 Mini uses a CH340, and its maker WCH has the driver here: https://www.wch-ic.com/downloads/CH34XSER_MAC_ZIP.html
Download it, run the installer, and allow it if macOS asks you to in System Settings under Privacy & Security. On the Mac this was built on, the board did not show up as a serial port before the driver was installed.

Boards with a different USB serial chip (a CP2102 for example) need that chip's driver instead.

**Linux** (Debian, Ubuntu and relatives, on a 64-bit Intel or AMD PC)

```sh
sudo apt-get install git make gcc python3 pipx wget
pipx install esptool==4.8.1
pipx ensurepath                        # then open a new terminal
sudo usermod -aG dialout $USER         # lets you use the serial port, log out and in again afterwards
```

Linux needs no driver for the CH340, it comes with the kernel.

Check that it worked. This should print `4.8.1`:

```sh
esptool.py version
```

The version matters. `brew install esptool` and a plain `pipx install esptool` give you esptool 5, and the build stops there with `Specify the --chip argument`. If you need esptool 5 for other things, see [Troubleshooting](#troubleshooting).

### 2. Get the compiler

The ESP8266 needs its own compiler, `xtensa-lx106-elf-gcc`.
Espressif publishes a ready-made one, so there is nothing to build.
Put it in `~/esp8266`:

**macOS**

```sh
mkdir -p ~/esp8266 && cd ~/esp8266
curl -LO https://dl.espressif.com/dl/xtensa-lx106-elf-macos-1.22.0-100-ge567ec7-5.2.0.tar.gz
tar xzf xtensa-lx106-elf-macos-1.22.0-100-ge567ec7-5.2.0.tar.gz
```

**Linux**

```sh
mkdir -p ~/esp8266 && cd ~/esp8266
wget https://dl.espressif.com/dl/xtensa-lx106-elf-linux64-1.22.0-100-ge567ec7-5.2.0.tar.gz
tar xzf xtensa-lx106-elf-linux64-1.22.0-100-ge567ec7-5.2.0.tar.gz
```

Check that it worked. This should print `5.2.0`:

```sh
~/esp8266/xtensa-lx106-elf/bin/xtensa-lx106-elf-gcc -dumpversion
```

### 3. Get the source

```sh
git clone --recursive https://github.com/DavidM42/channel4.git
cd channel4
```

`--recursive` matters. Most of the build lives in a submodule (`esp82xx`), and without it `make` finds nothing to do.
If you already cloned without it, run `git submodule update --init --recursive`.

### 4. Build

Run this in the `channel4` folder:

```sh
make clean ESP_ROOT="$HOME/esp8266" ESP_GCC_VERS=5.2.0 ESPTOOL_PY=esptool.py
make all   ESP_ROOT="$HOME/esp8266" ESP_GCC_VERS=5.2.0 ESPTOOL_PY=esptool.py
```

The three settings tell the build where the compiler from step 2 is, which version it is, and to use the esptool from step 1.

You will see a lot of compiler warnings. That is normal.
It worked if the last line says `Successfully created esp8266 image.` and these two files exist:

```
image.elf-0x00000.bin
image.elf-0x10000.bin
```

Always run `make clean` before `make all` after you change `user.cfg`. The build does not notice changes in that file by itself.

### 5. Flash

Plug the board in and find its serial port.

| | Command | Typical port |
|---|---|---|
| macOS | `ls /dev/cu.*` | `/dev/cu.wchusbserial10` |
| Linux | `ls /dev/ttyUSB*` | `/dev/ttyUSB0` |

If nothing like that is listed, see [Troubleshooting](#troubleshooting). On a Mac the usual reasons are the missing driver from step 1 or a USB cable that only charges.

Put it in a variable so the commands below can be copied as they are:

```sh
PORT=/dev/ttyUSB0      # use your own port here
```

**The first time**, write everything: the firmware, the web page, and the settings area the ESP8266 system software needs.

```sh
esptool.py --port "$PORT" -b 460800 write_flash -fm dio -fs 4MB \
  0x00000  image.elf-0x00000.bin \
  0x10000  image.elf-0x10000.bin \
  0x80000  web/page.mpfs \
  0x3FB000 esp82xx/toolchain/esp_nonos_sdk/bin/blank.bin \
  0x3FC000 esp82xx/toolchain/esp_nonos_sdk/bin/esp_init_data_default_v08.bin \
  0x3FE000 esp82xx/toolchain/esp_nonos_sdk/bin/blank.bin
```

**After that**, when you only rebuilt the firmware, the first two files are enough:

```sh
esptool.py --port "$PORT" -b 460800 write_flash -fm dio -fs 4MB \
  0x00000 image.elf-0x00000.bin \
  0x10000 image.elf-0x10000.bin
```

It worked if every file ends with `Hash of data verified.`

Three things worth knowing:

- **`-fs 4MB` is required.** Without it the firmware believes it has 1 MB of flash and looks for its settings in the wrong place.
- **These addresses are for 4 MB of flash**, which is what a D1 Mini has. `esptool.py --port "$PORT" flash_id` tells you what your board has. Other sizes were not tested here.
- **Use these commands instead of `make burn`.** The make targets leave out `-fs 4MB`, and they report success even when flashing failed.

### 6. Watch TV

1. Connect the wire to the pin labeled **RX** (GPIO3), best through [the filter](#the-filter-at-the-pin), and power the board from any USB supply.
2. Switch the TV to VHF band I (VHF-L, VL) and tune to channel E4, 62.5 MHz. On a set with a tuning wheel, turn slowly through the lower part of the band until the picture appears.
3. Set brightness so the background of a text screen is just black, then contrast so the text is crisp.

If `START_SILENT` is switched on in `user.cfg`, there is no picture until something asks for one. Join the board's WiFi network (see below) and open http://192.168.4.1/d/issue?CD to start the demo, or use the "Set Current" button on the web page.

The board also opens a WiFi network called `ESP_` followed by six characters. Join it and open http://192.168.4.1 for the web interface. Its "NTSC" button lets you freeze the demo on one screen, which makes adjusting the TV much easier.

### Updating over WiFi

Once a board runs this firmware and is on your network, new firmware can go on without USB:

```sh
python3 web/execute_reflash.py 192.168.1.50
```

That sends the two image files from the current folder. `make netburn IP=192.168.1.50`, with the same `ESP_ROOT=...` settings as in step 4, builds first and then does the same.

What happens:

1. It checks that the new firmware can go on this way, and whether the board already runs it.
2. It stops the TV signal, which disturbs the board's WiFi.
3. It puts both images into a spare part of the flash, reads them back and compares.
4. It tells the board to copy them over its firmware. The board checks them once more before it does.
5. It waits for the board to restart and reads its flash back.

Nothing on the board changes before step 4, and `--dry-run` stops before it.

**Step 4 takes about ten seconds. If the power fails in that time, the board does not start any more** and has to be flashed over USB.

The web page and the settings, the WiFi network among them, stay as they are.

## Options

All of these are lines in `user.cfg`. A `#` in front switches a line off.

| Line in `user.cfg` | What it does |
|---|---|
| `OPTS += -DPAL` | PAL timing: 625 lines, 50 fields per second. Off means NTSC. |
| `OPTS += -DMONOCHROME` | Black and white only. No colorburst, and the colors become shades of gray. |
| `OPTS += -DFBH=264` | Full height PAL picture, 264 lines instead of 220. The web page then runs out of memory, see [Picture size and memory](#picture-size-and-memory). |
| `OPTS += -DWHITE_BORDER` | Paints the visible area left, right and above the picture bright instead of black. |
| `OPTS += -DBORDER_LEVEL=13` | How bright that border is. Only used together with `WHITE_BORDER`. |
| `OPTS += -DSTART_SILENT` | No TV signal after power-up. It starts with the first text or demo command, see [Signal only when needed](#signal-only-when-needed). |

After changing any of them: `make clean`, `make all`, flash.

### Black and white only

On a black and white TV the NTSC color information only gets in the way. The colors show up as hatching, and the colorburst sits at a different level than black right where some TVs take their black reference.

With `MONOCHROME` there is no colorburst, and colors 0 to 15 become plain grays:

- 0 is black and 10 is white, as before.
- 2 and 8 are still the half black, half white ones that the sharp text uses.
- 3 to 7, 9 and 11 to 15 run from dark to bright.

A single pin can only be on or off, so only a few brightness levels come out clean. On channel E4 that is 8 grays between black and white, and some neighboring color numbers share a gray.

Both color tables live in `tablemaker/broadcast_tables.c`. The option picks one of them.

### Bright border

Many small TVs, most black and white portables among them, do not hold their black level. A mostly dark picture like the text screens comes out as light gray text on a slightly darker gray.

Try the brightness and contrast controls of the TV first. That is usually enough.

If it is not, `WHITE_BORDER` gives the TV something bright to go by on every screen, without taking anything away from the picture. White (`BORDER_LEVEL=10`, the default) works best but glows on a small tube. With `MONOCHROME`, 13 is a light gray and a good place to start.

The lines below the picture always stay black. Bright lines running right up to the vertical sync made the whole picture bounce on the TV this was tried on.

### Picture size and memory

The picture is 220 lines high by default, also for PAL. It sits in the middle of the screen with a black strip above and below, and the text screen has 14 lines.

`FBH=264` fills a PAL screen and gives the text screen 17 lines. The 44 extra lines cost 5 kB of RAM, and the web page needs that memory. Measured with a clean WiFi link (RX pin silent, see [WiFi and the TV signal](#wifi-and-the-tv-signal)), loading the web page the way a browser does:

| Build | Page loads that completed | Lowest free memory |
|---|---|---|
| 220 lines (default) | 8 of 8 | 2.6 kB |
| 264 lines | 0 of 8 | 0.5 kB |

Single small requests, like the text commands from Home Assistant, worked with both: 30 of 30.

To see how much memory is free on your board, open `http://<board>/d/issue?I`. It is the last number.

### Signal only when needed

With `START_SILENT` the RX pin stays silent after power-up. The TV gets nothing, and the board's WiFi is not disturbed by the TV signal.

The signal starts when something asks for a screen, and stops on request:

| What | TV signal |
|---|---|
| `CT`, `CX` (text screen) and `CD` (demo) | on |
| The web page: its "Set Current" button for the screen, and "Upload As" for a color (`CO`, `CV`) | on |
| `CS` | off |

Send the commands as `http://<board>/d/issue?CS` and so on, see [The commands behind it](#the-commands-behind-it).

While the signal is off, no screens are drawn and the demo stands still. It carries on where it stopped, or from its first screen after `CD`. The part that makes the TV lines keeps running, so the picture is there at once when the signal comes on.

Without `START_SILENT` the signal is on from the start, as in channel3. `CS` and the commands that start the signal again work either way.

## Antenna

The antenna is a plain wire on the **RX** pin. For the picture alone that is all you need. If you also want WiFi to work, put [the filter](#the-filter-at-the-pin) between the pin and the wire.

- **Start with 20 to 30 cm**, laid near the TV or its aerial. That is enough across a table or a room.
- **A full quarter wave is about 1.15 m** on channel E4. Only go there if the short wire gives a snowy picture.
- **Do not go longer than you need.** The pin puts out a raw 80 MHz bit stream. Next to the TV channel it also produces copies on other frequencies, one of them around 97.5 MHz in the FM radio band. A longer wire radiates all of them further, and you have no license for any of them. Keep it on your desk.

For other channels, a quarter wave in meters is about 71 divided by the frequency in MHz.

**Keep the wire away from the board's own antenna**, the zigzag trace at the end of the ESP8266 module. The TV signal disturbs the board's WiFi, see [WiFi and the TV signal](#wifi-and-the-tv-signal).

**The antenna can block flashing.** RX is also the pin the USB chip uses to talk to the ESP8266. A wire hanging free is no problem. A wire that is plugged into a TV aerial socket, or touches grounded metal, holds the pin down, and esptool ends with `No serial data received`. Unplug the far end of the wire while you flash.

## WiFi and the TV signal

The TV signal on the RX pin disturbs the board's own WiFi. Without a filter the web page loads slowly or not at all, text commands get lost for minutes at a time, and the board's own network is hard to find and join.

### The filter at the pin

Two parts between the RX pin and the antenna wire fix most of it:

```
RX pin ───[ 100 ohm ]───┬─── antenna wire
                        │
                      10 pF
                        │
                       GND
```

- **100 ohms in series**, soldered as close to the RX pin as you can.
- **10 pF to ground**, from the wire side of the resistor.

The TV channel passes almost unchanged. What is held back is the part of the signal up in the 2.4 GHz band, which is what the wire radiates straight into the board's WiFi antenna.

Keep the wire itself away from the end of the board that has the WiFi antenna.

### What was measured

On a D1 Mini with a wire antenna on RX, on a home WiFi. All three columns are the same firmware:

| | RX pin silent | TV signal, no filter | TV signal, with filter |
|---|---|---|---|
| Small web requests answered correctly | 30 of 30 | 25 of 30 | 29 of 30 |
| The same with the text screen showing | not measured | 35 of 90, with one silence of 5 minutes | 85 of 90, no silences |
| Files of the web page, one after another (126 kB) | all complete, 1 second | first page loads, the scripts stall after 4 kB | all complete, 8 seconds |
| Web page loaded the way a browser does | 8 of 8 | did not complete | 5 of 8 |
| Board's own network shows up in WiFi scans | 10 of 10 | 8 of 16, with long gaps | not measured |

So the filter makes WiFi usable, but not as good as with the pin silent. Text commands get through, and the web page loads, sometimes only at the second try.

It is not the processor load and not memory. With the whole video generator running and only the pin switched off, WiFi was fine, and free memory was the same. Moving the board's network to another WiFi channel (6 or 11 instead of 1) did not cure it either.

## PAL

### What PAL means here

- **Timing is PAL.** 625 lines, 64 microseconds each, switched on with `-DPAL`. This part came with channel3.
- **There is no PAL color.** The color signal in the tables is NTSC. A PAL color set shows the picture in black and white, a black and white set never cared. With `MONOCHROME` the color signal is left out completely.
- **There is no sound.**
- **The picture is 232 x 220** in the sharp black and white mode that the text uses, and 116 x 220 with 16 colors or grays. A PAL screen has room for 264 lines, see [Picture size and memory](#picture-size-and-memory).
- **It is made for B/G sets**, the standard in most of continental Europe. French SECAM L sets use a different kind of modulation and will not show it. Sets that only have UHF, as many in the UK and Ireland do, cannot tune this low.

### Why 62.5 MHz

Channel E4 officially has its picture carrier at 62.25 MHz. This fork transmits 0.25 MHz above that, on purpose.

Every signal level is a fixed pattern of ones and zeros that repeats along the line. How often it repeats depends on the frequency:

| Frequency | Pattern repeats every | On the TV |
|---|---|---|
| 62.27 MHz, the closest possible to 62.25 | 176 bits | Coarse diagonal stripes over the whole picture |
| 62.5 MHz | 32 bits | Clean |
| 61.25 MHz, US channel 3 | 64 bits | What channel3 uses |

A long pattern beats against the carrier at a low frequency, and that shows as wide stripes. 62.5 MHz is exactly 25/32 of the 80 MHz bit clock, so the pattern is as short as it gets near E4. A TV tunes the quarter megahertz without complaint.

### Changing the channel

The frequency is set in `tablemaker/synthtables.c`:

```c
double MODULATION_Frequency = CHANNEL_E4;
```

Change it, then rebuild the tables and the firmware:

```sh
cd tablemaker && make synthtables && cd ..
make clean ESP_ROOT="$HOME/esp8266" ESP_GCC_VERS=5.2.0 ESPTOOL_PY=esptool.py
make all   ESP_ROOT="$HOME/esp8266" ESP_GCC_VERS=5.2.0 ESPTOOL_PY=esptool.py
```

Rules for picking a frequency:

- It has to be a multiple of 80/1408 MHz (about 0.0568 MHz), so that a whole number of cycles fits into the table.
- Prefer one that is a simple fraction of 80 MHz, for the reason above. In band I those are 47.5, 52.5, 57.5, 62.5 and 67.5 MHz (pattern of 32 bits) and 55 and 65 MHz (16 bits).
- `CHANNEL_3` gives you the original US channel 3 back.

Only 62.5 MHz and 62.27 MHz have been tried on a real TV here.

## Home Assistant

The firmware has a text screen that you fill over WiFi, one line at a time. Home Assistant can do that with its built-in `rest_command`, so there is nothing extra to install.

### 1. Put the board on your WiFi

Out of the box the board opens its own network. For Home Assistant to reach it, it has to join yours.

1. Join the board's `ESP_...` network and open http://192.168.4.1.
2. Open **Wifi Settings**, pick **Station**, enter the name (SSID) and password of your WiFi, and press **Change Settings**.
3. The board leaves its own network and joins yours. The first demo screen on the TV shows the address it got, on the line starting with `IP:`.
4. Tell your router to always give the board that address.

If the board cannot get onto your WiFi after a few tries, it opens its own network again so you can correct the settings.

If the page does not load completely, one address does the same as the form:

```
http://192.168.4.1/d/issue?W1%09YOUR-WIFI-NAME%09YOUR-PASSWORD
```

`%09` is what the firmware expects between the parts. Name and password together have to stay under about 60 characters. Like the form, this sends your password unencrypted over the board's open network.

Once the board is on your WiFi, open `http://<board>/d/issue?CW`. That makes sure the network is stored, so the board comes back to it after a power cut. The reply should start with `CW 1 1 1`.

### 2. Try it without Home Assistant

Open this in a browser, with the address of your board:

```
http://192.168.1.50/d/issue?CT00Hello+World
```

The TV switches to the text screen and shows `Hello World` on the top line. The browser shows `CT`.

### 3. Add the package to Home Assistant

1. Open [homeassistant/channel4.yaml](homeassistant/channel4.yaml) and replace `192.168.1.50` with the address of your board. It appears four times.
2. Copy the file to `packages/channel4.yaml` in your Home Assistant configuration folder.
3. Make sure `configuration.yaml` loads packages:

   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

4. Restart Home Assistant.

Do not paste the contents of the file into `configuration.yaml` instead. That file usually already has a `script:` line, Home Assistant only keeps the last one it finds, and then either this script or all your own scripts are missing. The log shows `contains duplicate key "script"` when that happens.

The script is listed under its name, **TV: show message**. `script.channel4_message` is its entity ID.

### 4. Use it

The package gives you two scripts and four commands.

| Name | What it does |
|---|---|
| `script.channel4_message` | Shows a message. Wraps long lines, handles line breaks, spells out umlauts. |
| `script.channel4_send` | Sets one line, or empties the screen if you give it no line. Tries up to three times if the board does not answer. The script above uses it. |
| `rest_command.channel4_line` | Sets one line and switches to the text screen. Line 0 is the top one. |
| `rest_command.channel4_clear` | Empties the text screen and switches to it. |
| `rest_command.channel4_demo` | Goes back to the demo. |
| `rest_command.channel4_stop` | Stops the TV signal. Any of the three above starts it again. |

For example, as the action of an automation:

```yaml
- service: script.channel4_message
  data:
    message: |-
      Washing machine
      is done
```

Or one line that changes while the rest stays:

```yaml
- service: rest_command.channel4_line
  data:
    line: 3
    text: "Living room {{ states('sensor.living_room_temperature') }} C"
```

### Recipes from Mealie

A second package shows a [Mealie](https://mealie.io) recipe on the TV, first the ingredients and then the steps. You start it from the recipe in Mealie and page through it from Home Assistant. It needs the package from step 3.

1. Copy [homeassistant/channel4_mealie.yaml](homeassistant/channel4_mealie.yaml) to `packages/channel4_mealie.yaml`, next to `channel4.yaml`, and restart Home Assistant.
2. Allow Mealie to reach Home Assistant. Mealie does not send anything to addresses inside your home network unless you list them. Give the Mealie container this setting, with the address of Home Assistant, and start it again:

   ```yaml
   environment:
     HTTP_ALLOW_LIST: 192.168.1.10
   ```

3. In Mealie, open the Data Management page, go to the recipe actions and create one:

   | Field | Value |
   |---|---|
   | Title | `Show on TV` |
   | Type | `post` |
   | URL | `http://192.168.1.10:8123/api/webhook/channel4_recipe` |

4. Open a recipe, and pick **Show on TV** from the recipe actions in its menu.

The TV shows the ingredients:

```
Kaesespaetzle            Ingredients

Teig:
- 400 g Mehl Type 405
- 4 Eier
- 1 1/2 TL Salz
- 1/4 l Wasser lauwarm

Zum Ueberbacken:
- 250 g Bergkaese frisch gerieben,
  am besten eine Mischung aus
  Emmentaler und wuerzigem Bergkaese
```

The steps follow, each on its own screen with `Step 1/3` in the top line. Ingredients or a step that are longer than 12 lines continue on the next screen, and the top line then reads `Ingredients (1/2)` or `Step 2/3 (1/2)`. These scripts move through the screens:

| Name | What it does |
|---|---|
| `script.channel4_recipe_next` | Goes to the next screen. It stays on the last one. |
| `script.channel4_recipe_previous` | Goes to the previous screen. It stays on the first one. |
| `script.channel4_recipe_show` | Shows the current screen again, for example after another message. With `page` it jumps to that screen. |

Put them on a dashboard as buttons, or on a wireless button next to the stove.

`sensor.channel4_recipe` has the name of the recipe, and `counter.channel4_recipe_page` the number of the screen that is showing. Both are still there after a restart of Home Assistant. When you are done, `rest_command.channel4_demo` or `rest_command.channel4_stop` takes the recipe off the TV.

Good to know:

- **Special characters are spelled out.** `½` becomes `1/2`, `180 °C` becomes `180 C`, accents are dropped, and Markdown bold loses its stars. What is left over becomes `?`.
- **Amounts are not scaled.** If you set the recipe to twice the amount in Mealie, the TV still shows the amounts as written, with a line at the top that says so.
- **Mealie does not tell you if the action failed.** It only writes it to its own log, see [Troubleshooting](#troubleshooting).
- **The webhook only takes requests from your home network.** If Mealie runs somewhere else, see below.
- **This was tried with Mealie 3.28 and Home Assistant 2026.9**, with a program standing in for the board. Mealie versions that send the recipe on its own, without the wrapping around it, are handled too, but that was only tried with a made-up recipe.

#### If Mealie is not in your home network

When Mealie reaches Home Assistant from outside, for example through a Tailscale Funnel, Home Assistant Cloud or a reverse proxy, Home Assistant sees a request from the internet. It answers `200` and drops it. Mealie has no error to log, and nothing happens. The Home Assistant log shows `Received remote request for local webhook channel4_recipe`.

Change two lines of the trigger in `channel4_mealie.yaml` and reload the automations:

```yaml
        webhook_id: 3f9c1b7e52a44d0c9a6e8b1d2c7f4a10   # your own, from: openssl rand -hex 16
        local_only: false
```

Use the new ID in the URL of the recipe action too. The address is now open to the internet and the ID is its only password, so do not keep `channel4_recipe` or the example above. `HTTP_ALLOW_LIST` is not needed for a public address.

### The commands behind it

These are ordinary channel3 custom commands, so anything that can open a web address can use them. Put them after `http://<board>/d/issue?`.

| Command | What it does | Reply |
|---|---|---|
| `CT` + two digits + text, like `CT03Hello` | Puts the text on that line and shows the text screen. No text empties the line. | `CT`, or `!CT` if there is no such line |
| `CX` | Empties all lines and shows the text screen. | `CX` |
| `CD` | Goes back to the demo, starting with its first screen. | `CD` |
| `CS` | Stops the TV signal. `CT`, `CX`, `CD` and the web page start it again. | `CS` |
| `CW` | Stores the WiFi network the board is on, if it is not stored yet. | `CW`, then four numbers: mode now, mode stored (1 is on a network, 2 is its own access point), 1 if the stored network is the one in use, free memory |

The same commands also work as UDP packets to port 7878, without the address length limit below.

### Limits

- **36 characters per line.** Longer text is cut off. There are 14 lines (00 to 13), or 17 with `-DFBH=264`.
- **Web addresses are cut at 78 characters** by the firmware. That leaves 65 for the text after it has been encoded. Write spaces as `+`, which costs one character instead of the three of `%20`. The package does that for you.
- **The font only has plain ASCII.** German umlauts are spelled out (`ä` becomes `ae`, `ß` becomes `ss`). Any other special character becomes `?`.
- **The text is gone after a power cut.** The board starts with the demo again.
- **There is no password.** Everybody on your network can write on your TV.
- **A command can get lost.** With the text screen showing and [the filter](#the-filter-at-the-pin) fitted, 85 of 90 requests were answered correctly. Without the filter it was 35 of 90, with minutes of silence in between. `script.channel4_message` and `script.channel4_send` try each command up to three times. The `rest_command`s do not.

## Troubleshooting

| What you see | What to do |
|---|---|
| `make` does nothing, complains about missing files, or says the modules were not checked out | The submodule is missing. Run `git submodule update --init --recursive`. |
| `bad CPU type in executable` on a Mac | Install Rosetta: `softwareupdate --install-rosetta`. |
| The build stops with `Specify the --chip argument` | You have esptool 5. Install 4.8.1 as in step 1. If you want to keep 5, build with `ESPTOOL_PY="esptool.py --chip esp8266"` instead, that gives the same two files. Flashing with esptool 5 was not tried. |
| You changed `user.cfg` and nothing changed | Run `make clean` before `make all`. |
| No serial port appears when you plug the board in, on a Mac | Install the CH340 driver from step 1: https://www.wch-ic.com/downloads/CH34XSER_MAC_ZIP.html. If macOS asked to allow it, check System Settings under Privacy & Security, then unplug the board and plug it in again. If there is still no port, try another USB cable, many only charge. |
| No serial port appears when you plug the board in, on Linux | Try another USB cable, many only charge. On Ubuntu, the `brltty` package is known to grab these USB serial chips, remove it if you do not need it. |
| `Permission denied` on the port on Linux | Add yourself to the `dialout` group (step 1) and log in again. |
| `No serial data received` | The antenna is holding the RX pin down. Unplug its far end while flashing. See [Antenna](#antenna). |
| `No serial data received` with nothing connected to RX | The serial input of the board may be damaged. A board that still runs this firmware and is on your network can be updated without it, see [Updating over WiFi](#updating-over-wifi). |
| Flashing worked, but there is no picture and no WiFi network | Flash again with the long first-time command, including `-fs 4MB`. |
| The web page does not load | `web/page.mpfs` is not on the board. Flash with the long first-time command. |
| The web page loads slowly, or only shows "Introduction" and "NTSC" | The TV signal disturbs the board's WiFi. Fit [the filter at the pin](#the-filter-at-the-pin). With it the page can still need a second try. |
| The board's own network `ESP_...` is missing from the list, or joining it fails | Same cause, fit the filter. Without it the network comes and goes, try again a few times. |
| Text from Home Assistant does not arrive for minutes | Same cause, fit the filter. |
| The board is back on its own network after a restart | Put it on your WiFi again, then open `http://<board>/d/issue?CW`. The reply should start with `CW 1 1 1`. |
| The three `rest_command`s are there but `script.channel4_message` is missing | The file was pasted into `configuration.yaml`, which already has a `script:` line. Use it as a package, see [step 3](#3-add-the-package-to-home-assistant). In the list of scripts it is called "TV: show message". |
| Home Assistant warns `Setup of package 'channel4' failed: integration 'rest_command' has duplicate key 'url'` | The three commands are defined twice, in the package and somewhere else, usually a copy pasted into `configuration.yaml`. Remove that copy and restart. |
| Home Assistant cannot reach the board | Open `http://<board>/d/issue?CC` in a browser. If that does not show `CC`, the address is wrong or the board is not on your WiFi. Its address is on the first demo screen. |
| The recipe action in Mealie does nothing | Look at the log of Mealie. `invalid request on local resource` means Mealie is not allowed to reach Home Assistant, set `HTTP_ALLOW_LIST` as in [Recipes from Mealie](#recipes-from-mealie). If the log is clean and Mealie reaches Home Assistant from outside your home network, the webhook has to be opened, see [If Mealie is not in your home network](#if-mealie-is-not-in-your-home-network). Otherwise check the address of the action. If your `configuration.yaml` has no `default_config:` line, add a line `webhook:`. |
| Text from Home Assistant ends in `?` or odd characters | The line was too long for the firmware's 78 character address limit. Use `script.channel4_message`, which keeps lines short enough. |
| Coarse diagonal stripes | The carrier frequency has a long bit pattern. See [Why 62.5 MHz](#why-625-mhz). |
| Text on a gray background instead of black | Turn the brightness of the TV down and the contrast up. If that is not enough, try `WHITE_BORDER`. |
| The picture rolls or bounces | Adjust V-hold on the TV to the middle of the range where the picture stands still. |

## How it works

Everything from here on is the original channel3 README. It describes NTSC and US channel 3. Where it says 61.25 MHz, this fork uses 62.5 MHz.

One demo screen is switched off in this fork: the "38x14 TEXT MODE" intro that came before the framebuffer copy test. Its text did not come out right on the test TV. The list of screens below is adjusted to match.

If you are looking for the kolumbus.fi NTSC/PAL mirror, see it here: https://cnlohr.github.io/channel3/ntsc_pal_frame_documentation/pal_ntsc_from_kolumbus_fi_pami1.html

### Background and RF

This uses the I2S Bus in the same way the esp8266ws2812i2s project does.  Difference is it cranks the output baud to 80 MHz.  We set up DMA buffers and let the CPU fill them as they pass through one line at a time.  The DMA interrupt fills in the buffers one word at a time.  The I2S bus shifts those buffers out at 80 MHz!

You may say "But nyquist says you can't transmit or receive frequencies at more than 1/2 the sample rate (40 MHz in this case).  To a degree that is true.  Some people thought it may be overtones, but what happens in reality something stranger happens.  Everything you transmit is actually mirrored around 1/2 the sample rate (40 MHz).  So, transmitting 60 MHz on an 80 MHz bitclock creates a waveform both at 60 as well as 20.  This isn't perfect.  Some frequencies line up to the 80 MHz well, others do not.

We store a bit pattern in the "premodulated_table" array.  This contains bitstreams for various signals, such as the "sync" level or "colorbust" level, or any of the visual colors.  This table's length of 1408 bits per color was chosen so that when sent out one bit at a time at 80 MHz, it works out to an even multiplier of the NTCS chroma frequency of 315.0/88.0 MHz, or 3.579545455 MHz.  You can calculate this by taking 1408/80MHz = 17.6us * 3.579545 MHz = 63 cycles, exactly.  Conveniently, it also works out to an even multiplier of 61.25 MHz, Channel 3's luma center.  17.6us * 61.25 MHz = 1078 cycles, exactly! When you modulate arbitrary frequencies, sometimes the cycles come out very uneven. 

In order to generate luma (the black and white portion) we modulate 61.25 MHz.  If we generate a strong signal, it is viewed as a very "dark", and a weak signal is a very "bright."  This means when we want to send out a sync pulse, we modulate it as loud as we can... when we want to modulate white, we put out barely any signal at all.  One thing you will notice is dot pour.  This is because the signal we are sending is so terrible.  The chroma signal is very dirty and has a repeating intensity pattern.  While the chroma lines up to the 1408 bit-wide repeating patten, the total number of pixels on the screen does not.  This causes the patterns created to roll down the screen.

In order to generate color, we need to modulate in a chroma signal, 3.579MHz above the baseband.  The chroma is synchronized by a colorburst at the beginning of each line.  This also sets the level for the chroma.  Then, during the line, we can either choose a "color" that has a high coefficient at the chroma level, or a low one.  This determines how vivid the color is.  We can change phase to change the color's hue.

This is basically a 1-bit dithering DAC, operating at a frequency below the nyquist, trying to encode luma and color at the same time.  Don't be surprised that the quality's terrible.

### Code Layout

Tables for handling the line-buffer state machine are (generated/stored?) in MayCbTables.h/c, and similar tables for creating the on-wire signal encoding are in synthtables.c.

Functions to set up the DMA transfers, refill the buffers when they become empty, and change what kind of line should be sent based on the framebuffer contents are in video_broadcast.c. These functions handle all of the modulation.  This sets up the DMA, and an interrupt that is called when the DMA finishes a block (equal to one line).  Upon completion, it uses CbTable to decide what function to call to fill in the line.  The interrupt fills out the next line for DMA which keeps going.

The framebuffer is updated by various demo screens located in user_main.c.

custom_commands.c contain the custom commands used for the NTSC-specific aspects.  Using the common websockets interface there are two added commands.  These include "CO" and "CV" which set the operation mode (CO) and allow users to change the modulation table from a web interface (CV).

### Demo screens

The following demo screens are available.  They normally tick through one after another (except ones after 10), unless the user disables this in the web browser.

### Screen Modes

1. Basic intro screen, shows IP address if available.
2. ESP8266 Features
3. Framebuffer copy test.  Beware, running this screen too long deliberately will cause a crash. <!-- channel3 original: "Intro to and completion of framebuffer copy test."  The intro screen ("38x14 TEXT MODE ...on 232x220 gfx") is commented out in user/user_main.c in this fork, the demo goes straight to the copy test. -->
6. Draw a bunch of lines... IN COLOR!
7. Matrix-based 3D engine demo.
8. Dynamic 3D mesh demo.
9. Pitch for this project's github.
10. Color screen with 16 color balls.
11. 4x4 color swatches, useful for when you're messing with colors in the web GUI.

### Web interface

The web interface is borrowing the web interface from esp8266ws2812i2s.  Power on the ESP, connect to it, then, point your web browser to http://192.168.4.1.  It has a new button "NTSC."  This gives you the option to allow demo to continue from screen to screen, or freeze at a specific screen.  You can specify the screen.  Additionally, for RF testing, you can jam a color.  Whenever the color jam is set to something 0 or above, it turns off all line drawing logic, and simply outputs that color continuously.  This will prevent TV sets from seeing it, however, you can see it on other RF equipment.

It also has an interactive Javascript webworker system that lets you write code to make a new color!  You can create a new bitstream that will be transmitted when a specific color is hit.  You can edit the code and it is effective as you type.  It automatically re-starts the webworker every time you change it.

You should only output -1 or +1 as that is all the ESP can output.  It will then run a DFT with a randomized window over a frequency area you choose.  Increase the DFT window, and it will increase your q (or precision).  Decrease, it decreases your q.  This is to help see how receivers like the TV really understand the signal and help illustrate how wacky this really is.

You can try it in your own browser using this link: http://cnlohr.github.io/channel3/web/page/index.html  Click NTSC and go to town.

### Rawdraw and 3D

For all the 3D and text, I'm using a new modified version of my "rawdraw" library ( http://github.com/cnlohr/rawdraw ) for 3D I'm using fixed point numbers, with 256 as the unit value, and the bottom 8 bits are the fractional component.

### PAL Modification

To allow for PAL broadcasts, the timings in the video_broadcast-library (formerly ntsc_broadcast) were modified. Since I only wanted to use this with a black an white TV, and PAL colour is actually quite complicated to do digitally, I didn't modify the broadcast_tables (synthtables.c). So the library broadcasts a PAL compliant B/W-Signal with NTSC Colour information (kind of like NTSC50).

To enable PAL broadcasting you need to enable ```OPTS += -DPAL``` in user.cfg. 

### Youtube video

Here is the original youtube video on this project:

[![NTSC Video on the ESP8266](http://img.youtube.com/vi/SSiRkpgwVKY/0.jpg)](http://www.youtube.com/watch?v=SSiRkpgwVKY)

Here is the new video (with COLOR):

[![Broadcasting COLOR Channel 3 on an ESP](http://img.youtube.com/vi/bcez5pcp55w/0.jpg)](http://www.youtube.com/watch?v=bcez5pcp55w)
