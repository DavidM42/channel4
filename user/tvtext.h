//Text screen that gets filled in from outside, for example by Home Assistant.
//The commands for it (CT, CX, CD) are in custom_commands.c, the screen is drawn in user_main.c.

#ifndef _TVTEXT_H
#define _TVTEXT_H

//Which showstate the text screen is.
#define TVTEXT_SHOWSTATE 12

#include "video_broadcast.h"

//What fits on the screen at text scale 2: a character is 6 pixels wide, a line is 14 high.
//That is 14 lines on the normal 220 line framebuffer, and 17 with FBH=264.
#define TVTEXT_COLS 36
#define TVTEXT_LINES ( ( FBH - 36 ) / 14 + 1 )

extern char tvtext[TVTEXT_LINES][TVTEXT_COLS+1];

//Empties all lines.
void TVTextClear();

//Puts text (len bytes, no terminator needed) into a line, cut off at TVTEXT_COLS.
//Returns 0, or -1 if there is no such line.
int TVTextSetLine( int line, const char * text, int len );

#endif
