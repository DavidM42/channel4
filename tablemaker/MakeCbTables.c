#include <stdio.h>
#include <string.h>
#include <stdint.h>

#define PAL_LINES 625
#define NTSC_LINES 525

#define FT_STA_d 0
#define FT_STB_d 1
#define FT_B_d 2
#define FT_SRA_d 3
#define FT_SRB_d 4
#define FT_LIN_d 5
#define FT_CLOSE_d 6
#define FT_MAX_d 7

//Writes a line table to CbTable.c, two lines to a byte.
static void WriteTable( FILE * f, const char * name, const uint8_t * table, int lines )
{
	int x;
	fprintf( f, "uint8_t %s[%d] = {", name, (lines+1)/2 );
	for( x = 0; x < (lines+1)/2; x++ )
	{
		if( (x & 0x0f) == 0 )
		{
			fprintf( f, "\n\t" );
		}
		fprintf( f, "0x%02x, ", table[x*2+0] | ( table[x*2+1]<<4 ) );
	}
	fprintf( f, "};\n" );
}

int main()
{
// PAL
	//Because we're odd, we have to extend this by one byte.
	uint8_t CbLookupPAL[PAL_LINES+1]; 
	memset( CbLookupPAL, 0, sizeof(CbLookupPAL) );
	int x = 0;

	#define OVERSCAN_TOP 30
	#define OVERSCAN_BOT 10
	
	//Setup the callback table.
	for( x = 0; x < 2; x++ )
		CbLookupPAL[x] = FT_STB_d;
	CbLookupPAL[x++] = FT_SRB_d;
	for( ; x < 5; x++ )
		CbLookupPAL[x] = FT_STA_d;

	for( ; x < 5+OVERSCAN_TOP; x++ )
		CbLookupPAL[x] = FT_B_d;
	for( ; x < 310-OVERSCAN_BOT; x++ ) // 250
		CbLookupPAL[x] = FT_LIN_d;
	for( ; x < 310; x++ )
		CbLookupPAL[x] = FT_B_d;
	for( ; x < 312; x++ )
		CbLookupPAL[x] = FT_STA_d;

	//begin odd field
	CbLookupPAL[x++] = FT_SRA_d;
	for( ; x < 315; x++ )
		CbLookupPAL[x] = FT_STB_d;
	for( ; x < 317; x++ )
		CbLookupPAL[x] = FT_STA_d;

	for( ; x < 317+OVERSCAN_TOP; x++ )
		CbLookupPAL[x] = FT_B_d;
	for( ; x < 622-OVERSCAN_BOT; x++ )//562
		CbLookupPAL[x] = FT_LIN_d;
	for( ; x < 622; x++ )
		CbLookupPAL[x] = FT_B_d;
	for( ; x < 624; x++ )
		CbLookupPAL[x] = FT_STA_d;
	CbLookupPAL[x++] = FT_CLOSE_d;
	CbLookupPAL[x++] = FT_CLOSE_d;

// PAL without interlacing (NO_INTERLACE)
	//Above, the second field starts half a line late, which is what makes a TV draw it between the lines of the
	//first one.  Both fields show the same framebuffer, so the picture jumps up and down by half a line 25 times
	//a second.  Here the second field is a copy of the first.  It starts on a full line and lands on the same
	//TV lines.  That is 312 lines per field, like the home computers did it, and 624 per frame.
	uint8_t CbLookupPALNoInterlace[PAL_LINES+1];
	memset( CbLookupPALNoInterlace, 0, sizeof(CbLookupPALNoInterlace) );
	for( x = 0; x < 312; x++ )
		CbLookupPALNoInterlace[x] = CbLookupPALNoInterlace[x+312] = CbLookupPAL[x];
	CbLookupPALNoInterlace[623] = FT_CLOSE_d; //Ends the frame.  On the TV it is the same line as the FT_STA it replaces.
	CbLookupPALNoInterlace[624] = FT_CLOSE_d;

// NTSC
	//Because we're odd, we have to extend this by one byte.
	uint8_t CbLookupNTSC[NTSC_LINES+1]; 
	memset( CbLookupNTSC, 0, sizeof(CbLookupNTSC) );
	x = 0;

	//Setup the callback table.
	for( x = 0; x < 3; x++ )
		CbLookupNTSC[x] = FT_STA_d;
	for( ; x < 6; x++ )
		CbLookupNTSC[x] = FT_STB_d;
	for( ; x < 9; x++ )
		CbLookupNTSC[x] = FT_STA_d;
	for( ; x < 24+6; x++ )
		CbLookupNTSC[x] = FT_B_d;
	for( ; x < 256-15; x++ )
		CbLookupNTSC[x] = FT_LIN_d;
	for( ; x < 263; x++ )
		CbLookupNTSC[x] = FT_B_d;

	//263rd frame, begin odd sync.
	for( ; x < 266; x++ )
		CbLookupNTSC[x] = FT_STA_d;

	CbLookupNTSC[x++] = FT_SRA_d;

	for( ; x < 269; x++ )
		CbLookupNTSC[x] = FT_STB_d;

	CbLookupNTSC[x++] = FT_SRB_d;

	for( ; x < 272; x++ )
		CbLookupNTSC[x] = FT_STA_d;
	for( ; x < 288+6; x++ )
		CbLookupNTSC[x] = FT_B_d;
	for( ; x < 519-15; x++ )
		CbLookupNTSC[x] = FT_LIN_d;
	for( ; x < NTSC_LINES-1; x++ )
		CbLookupNTSC[x] = FT_B_d;
	CbLookupNTSC[x] = FT_CLOSE_d;

	FILE * f = fopen( "CbTable.h", "w" );
	fprintf( f, "#ifndef _CBTABLE_H\n\
#define _CBTABLE_H\n\
\n\
#include <c_types.h>\n\
\n\
#define FT_STA_d 0\n\
#define FT_STB_d 1\n\
#define FT_B_d 2\n\
#define FT_SRA_d 3\n\
#define FT_SRB_d 4\n\
#define FT_LIN_d 5\n\
#define FT_CLOSE 6\n\
#define FT_MAX_d 7\n\
\n\
uint8_t CbLookupPAL[%d];\n\
uint8_t CbLookupNTSC[%d];\n\
\n\
#ifdef PAL\n\
#define VIDEO_LINES %d\n\
#define CbLookup CbLookupPAL\n\
#else\n\
#define VIDEO_LINES %d\n\
#define CbLookup CbLookupNTSC\n\
#endif\n\
\n\
#endif\n\n", (PAL_LINES+1)/2, (NTSC_LINES+1)/2, PAL_LINES,  NTSC_LINES );
	fclose( f );

	f = fopen( "CbTable.c", "w" );
	fprintf( f, "#include \"CbTable.h\"\n\n" );

	fprintf( f, "#ifdef NO_INTERLACE\n" );
	WriteTable( f, "CbLookupPAL", CbLookupPALNoInterlace, PAL_LINES );
	fprintf( f, "#else\n" );
	WriteTable( f, "CbLookupPAL", CbLookupPAL, PAL_LINES );
	fprintf( f, "#endif\n" );
	WriteTable( f, "CbLookupNTSC", CbLookupNTSC, NTSC_LINES );

	return 0;
}

