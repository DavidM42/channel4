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

//Pausing the TV signal while a screen gets filled.  The signal on the pin slows the board's own WiFi down a lot,
//so the lines of a screen arrive much faster without it.  CH starts the pause, CG ends it and shows the text.
//If CG never comes, the signal comes back by itself this long after the last text command, in tenths of a second.
//It has to be longer than the sender waits for a reply (5 s in the Home Assistant package), or one slow request ends the pause.
#define TVTEXT_HOLD_TICKS 80

extern uint8_t tvtext_hold; //Tenths of a second the pause still lasts, 0 if there is none.

//Starts the pause, or makes a running one last the full time again.
void TVTextHold();

//Ends the pause if there is one, and shows the text screen.
void TVTextShow();

//Call every tenth of a second.
void TVTextTick();

#endif
