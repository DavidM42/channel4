//Text screen that gets filled in from outside.  See tvtext.h.

#include <c_types.h>
#include "tvtext.h"

char tvtext[TVTEXT_LINES][TVTEXT_COLS+1];
uint8_t tvtext_hold;

extern uint8_t showstate;

void ICACHE_FLASH_ATTR TVTextHold()
{
	tvtext_hold = TVTEXT_HOLD_TICKS;
	VideoTransmit( 0 );
}

void ICACHE_FLASH_ATTR TVTextShow()
{
	tvtext_hold = 0;
	showstate = TVTEXT_SHOWSTATE;
	VideoTransmit( 1 );
}

void ICACHE_FLASH_ATTR TVTextTick()
{
	if( tvtext_hold && !--tvtext_hold )
	{
		TVTextShow();
	}
}

void ICACHE_FLASH_ATTR TVTextClear()
{
	int i;
	for( i = 0; i < TVTEXT_LINES; i++ )
	{
		tvtext[i][0] = 0;
	}
}

//The font only has 7-bit ASCII.  German umlauts arriving as UTF-8 (0xc3 and one of these) get spelled out,
//everything else it doesn't have turns into '?'.
static const char umlauts[] = "\xa4" "ae" "\xb6" "oe" "\xbc" "ue" "\x84" "Ae" "\x96" "Oe" "\x9c" "Ue" "\x9f" "ss";

int ICACHE_FLASH_ATTR TVTextSetLine( int line, const char * text, int len )
{
	char * out;
	int o = 0;
	int i, k;

	if( line < 0 || line >= TVTEXT_LINES )
	{
		return -1;
	}

	out = tvtext[line];

	for( i = 0; i < len && o < TVTEXT_COLS; i++ )
	{
		unsigned char c = text[i];

		if( c == 0xc3 && i+1 < len )
		{
			for( k = 0; umlauts[k]; k += 3 )
			{
				if( (unsigned char)umlauts[k] == (unsigned char)text[i+1] ) break;
			}
			if( umlauts[k] )
			{
				out[o++] = umlauts[k+1];
				if( o < TVTEXT_COLS ) out[o++] = umlauts[k+2];
				i++;
				continue;
			}
		}

		if( (c & 0xc0) == 0x80 )
		{
			continue; //Rest of a UTF-8 character that already became a '?'
		}

		if( c >= 0x80 )
		{
			c = '?';
		}
		else if( c < ' ' || c == 127 )
		{
			c = ' ';
		}

		out[o++] = c;
	}

	out[o] = 0;
	return 0;
}
