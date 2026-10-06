//Copyright 2015 <>< Charles Lohr, see LICENSE file.

#include <commonservices.h>
#include <video_broadcast.h>
#include <esp82xxutil.h>
#include "../tablemaker/broadcast_tables.h"
#include "tvtext.h"
#include "user_interface.h"

extern uint8_t showstate;
extern uint8_t showallowadvance;
extern int8_t jam_color;
extern int framessostate;
extern int showtemp;

int ICACHE_FLASH_ATTR CustomCommand(char * buffer, int retsize, char *pusrdata, unsigned short len)
{
	char * buffend = buffer;

	switch( pusrdata[1] )
	{
	case 'C': case 'c': //Custom command test
	{
		buffend += ets_sprintf( buffend, "CC" );
		return buffend-buffer;
	}

	case 'o': case 'O':  //co xxyy   (where xx = current show state, yy = allow advancing)
	{
		//Show control
		char * bp = &buffer[3];
		uint8_t rh = 0;
		rh = fromhex1( *(bp++) );
		showstate = (rh << 4) | fromhex1( *(bp++) );
		rh = fromhex1( *(bp++) );
		showallowadvance = (rh << 4) | fromhex1( *(bp++) );
		rh = fromhex1( *(bp++) );
		jam_color = (rh << 4) | fromhex1( *(bp++) );
		VideoTransmit( 1 );
		break;
	}

	case 'v': case 'V': //cv xxnnnnnnnnnnnnn (where xx is the color #, nnnnnnnn is the color data)
	{
		int i;
		char * bp = &buffer[3];

		uint8_t ch = fromhex1( *(bp++) ); 
		ch = (ch<<4) | fromhex1( *(bp++) );

		if( ch >= PREMOD_SIZE )
		{
			buffend += ets_sprintf( buffend, "!CV" );
			break;
		}

		//XXX Todo: make sure we don't read off the end of the input array.
		for( i = 0; i < PREMOD_ENTRIES; i++ )
		{
			int k;
			uint32_t colval = 0;
			for( k = 0; k < 8; k++ )
			{
				colval = (colval<<4) | fromhex1( *(bp++) );
			}
			premodulated_table[i*PREMOD_SIZE + ch] = colval;
		}

		//Add the overspill bits.
		for( i = PREMOD_ENTRIES; i < PREMOD_ENTRIES_WITH_SPILL; i++ )
		{
			premodulated_table[i*PREMOD_SIZE + ch] = premodulated_table[(i-PREMOD_ENTRIES)*PREMOD_SIZE + ch];
		}

		VideoTransmit( 1 );
		break;
	}

	case 't': case 'T': //ctnntext   (where nn = line number, two decimal digits, text = what to put on that line)
	{
		//Sets one line of the text screen and shows that screen.
		//Read all of the input first, over HTTP the reply goes into the same buffer.
		int line = -1;
		if( len >= 4 && pusrdata[2] >= '0' && pusrdata[2] <= '9' && pusrdata[3] >= '0' && pusrdata[3] <= '9' )
		{
			line = ( pusrdata[2] - '0' ) * 10 + ( pusrdata[3] - '0' );
		}

		if( TVTextSetLine( line, &pusrdata[4], len - 4 ) )
		{
			buffend += ets_sprintf( buffend, "!CT" );
			return buffend-buffer;
		}

		showstate = TVTEXT_SHOWSTATE;
		VideoTransmit( 1 );
		buffend += ets_sprintf( buffend, "CT" );
		return buffend-buffer;
	}

	case 'x': case 'X': //cx   Empties the text screen and shows it.
	{
		TVTextClear();
		showstate = TVTEXT_SHOWSTATE;
		VideoTransmit( 1 );
		buffend += ets_sprintf( buffend, "CX" );
		return buffend-buffer;
	}

	case 'w': case 'W': //cw   Makes sure the WiFi network in use is the one the board comes back to after a restart.
	{
		//Replies: mode now, mode stored, whether the stored network is the one in use, free memory.  (Mode 1 = on a network, 2 = own access point)
		//The WiFi command stores the network too, but that was seen not to stick when memory was short.
		struct station_config now, stored;
		int same = 0;
		if( wifi_get_opmode() == 1 )
		{
			wifi_station_get_config( &now );
			wifi_station_get_config_default( &stored );
			if( ets_memcmp( now.ssid, stored.ssid, sizeof( now.ssid ) ) || ets_memcmp( now.password, stored.password, sizeof( now.password ) ) )
			{
				wifi_station_set_config( &now );
			}
			if( wifi_get_opmode_default() != 1 )
			{
				wifi_set_opmode( 1 );
			}
			wifi_station_get_config_default( &stored );
			same = !ets_memcmp( now.ssid, stored.ssid, sizeof( now.ssid ) ) && !ets_memcmp( now.password, stored.password, sizeof( now.password ) );
		}
		buffend += ets_sprintf( buffend, "CW\t%d\t%d\t%d\t%d", wifi_get_opmode(), wifi_get_opmode_default(), same, system_get_free_heap_size() );
		return buffend-buffer;
	}

	case 'd': case 'D': //cd   Back to the demo, from its first screen.
	{
		showstate = 0;
		showallowadvance = 1;
		framessostate = 0;
		showtemp = 0;
		VideoTransmit( 1 );
		buffend += ets_sprintf( buffend, "CD" );
		return buffend-buffer;
	}

	case 's': case 'S': //cs   Stops the TV signal.  Any command that shows something starts it again: CT, CX, CD, CO, CV.
	{
		VideoTransmit( 0 );
		buffend += ets_sprintf( buffend, "CS" );
		return buffend-buffer;
	}
	}
	return -1;
}
