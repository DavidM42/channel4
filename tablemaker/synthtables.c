/*
	Table synthesizer:  this tool creates bit tables for differen bit stream outputs.
	though the frequency we are synthesizing is above what we can actually create (f/2 and all)
	this will let you try and will alias just fine.  Just be sure to check its output against
	an FFT.
*/

#include <stdint.h>
#include <string.h>
#include <stdio.h>
#include <math.h>

#define PI2 (3.14159265359*2)

double eps = 0.01; //Used to help resolve and prevent issues at 0.
double NTSC_Frequency = 315.0/88.0;   //3.579545455 MHz

#define CHANNEL_2  55.22727272727  //Actually 55.25, but need to make it line up to the 1408 mark.
#define CHANNEL_3  61.25 //Channel 3 works out perfectly.
#define CHANNEL_4  67.272727273
#define CHANNEL_5  77.25
#define CHANNEL_E4 62.5 //European (CCIR B/G) channel E4.  Actually 62.25, but 62.5 repeats every 32 bits.  The closer 62.2727 repeats every 176 and beats visibly (diagonal stripes).

//To find precise frequency divisors... (1408/80)×67.25(nominal frequency) = 1183.6 ... round up.... 1184/(1408/80) = 67.272727273

double MODULATION_Frequency = CHANNEL_E4;


double BIT_Frequency = 80.0;
int samples = 1408;//1408;//+2; //+2 if you want to see   WARNING: This MUST be divisible by 32!
int overshoot = (32*7); //bits of overshoot (continue the table past the end so we don't have to keep checking to make sure it's ok)

// I tried initially without this, but it causes an extra reflection around the main carrier.  Turns out it's cleaner just to modulate directly to the carrier+chroma frequency.  This flag enables that.
#define DIRECT_CHROMA_CARRIER_SYNTHESIS


//ChromaValue, LumaValue = 0...??? 
//, ChromaShift, Luma are all 0..1
//Set boundary to a value to normalize Luma + Chroma.  Setting this to 0 will maximize both.
//Note that if ChromaValue == LumaValue, Chroma will not effect the signal.
//
//For all use of this function, I highly recommend checking the output at 160MHz (doubling)
//in an FFT, like http://sooeet.com/math/online-fft-calculator.php
//
//WARNING: These values are sort of inverted, as abscence of signal indicates value!
void WriteSignal( double LumaValue, double ChromaValue, double Boundary, double ChromaShift, int debug_output, uint32_t * raw_output, uint32_t mask )
{
	double t = 0;
	int i;
	int bitplace = 0;
	int byteplace = 0;

	for( i = 0; i < samples+overshoot; i++ )
	{
		double ModV = sin( ( MODULATION_Frequency * t ) * PI2 / 1000.0 + eps );
#ifdef DIRECT_CHROMA_CARRIER_SYNTHESIS
		double ChromaNV = sin( ((NTSC_Frequency+MODULATION_Frequency) * t ) * PI2 / 1000.0 + eps  + ChromaShift * PI2  );
		double Signal = ModV * LumaValue + ChromaNV * ChromaValue + Boundary;
#else
		double ChromaV = sin( (NTSC_Frequency * t ) * PI2 / 1000.0 + eps  + ChromaShift * PI2  );
		double Signal = ModV * (ChromaV*(ChromaValue)+LumaValue) + Boundary;
#endif

		if( Signal > 0 )
			raw_output[byteplace] |= (1<<(31-bitplace)) & mask;
		bitplace++;
		if( bitplace == 32 ) { bitplace = 0; byteplace++; }
		
		if( debug_output )
		{
			fprintf( stderr, "%d\n", ((Signal)>0)?1:-1 );
			fprintf( stderr, "%d\n", ((Signal)>0)?1:-1 );
		}
		t += 1000.0 / BIT_Frequency;
	}
}

#define TABLESIZE 18

//How much carrier a signal has (0 = none), measured at the modulation frequency.
double CarrierLevel( uint32_t * raw_output )
{
	double re = 0, im = 0;
	int i;
	for( i = 0; i < samples; i++ )
	{
		if( raw_output[i/32] & (1<<(31-(i&31))) )
		{
			double ph = MODULATION_Frequency * i / BIT_Frequency * PI2;
			re += cos( ph );
			im += sin( ph );
		}
	}
	return sqrt( re*re + im*im ) / samples;
}

//Writes the plain (no chroma) signal whose carrier comes closest to "carrier", on the scale of CarrierLevel.
//One bit can only hit a handful of levels cleanly.  Nudging the phase a little (eps) about doubles how many there are.
void WriteGray( double carrier, uint32_t * raw_output )
{
	uint32_t trial[(samples+overshoot)/32];
	double saveeps = eps;
	double besterr = 1e20, bestboundary = 1.0, besteps = eps;
	int e, b;

	for( e = 0; e < 9; e++ )
	for( b = 0; b <= 100; b++ )
	{
		eps = saveeps + e * 0.0125;
		memset( trial, 0, sizeof( trial ) );
		WriteSignal( 1.0, 0.0, 0.5 + b * 0.005, 0.0, 0, trial, 0xffffffff );
		double err = fabs( CarrierLevel( trial ) - carrier );
		if( err < besterr - 1e-9 )
		{
			besterr = err;
			bestboundary = 0.5 + b * 0.005;
			besteps = eps;
		}
	}

	eps = besteps;
	WriteSignal( 1.0, 0.0, bestboundary, 0.0, 0, raw_output, 0xffffffff );
	eps = saveeps;
}

//Writes all TABLESIZE signals into databuffer (which must be zeroed).
//If mono is set, this leaves out everything NTSC: there is no colorburst, and the colors turn into plain shades of gray.
void WriteTable( uint32_t * databuffer, int stride, int mono )
{
	int debug = 0;
	int i;

	WriteSignal( 1.0, 0.0, 0.7, 0.0, debug, &databuffer[stride*0], 0xffffffff ); //Black.  //-18.1 db
	WriteSignal( 1.0, 0.0, 1.0, 0.0, debug, &databuffer[stride*2], 0xffff0000 ); //White
	WriteSignal( 1.0, 0.0, 0.7, 0.0, debug, &databuffer[stride*2], 0x0000ffff ); //Black.  //-18.1 db
	WriteSignal( 1.0, 0.0, 1.0, 0.0, debug, &databuffer[stride*8], 0x0000ffff ); //White
	WriteSignal( 1.0, 0.0, 0.7, 0.0, debug, &databuffer[stride*8], 0xffff0000 ); //Black.  //-18.1 db
	WriteSignal( 1.0, 0.0, 1.0, 0.0, debug, &databuffer[stride*10], 0xffffffff ); //White
//BLACK
	WriteSignal( 1.0, 0.0, 0.85, 0.0, debug, &databuffer[stride*1], 0xffffffff );  //GRAY

	if( mono )
	{
		//The remaining colors become a gray ramp, dark to bright.  The carrier fades linearly from black's level down to nothing (white).
		static const int ramp[] = { 3, 4, 5, 6, 7, 9, 11, 12, 13, 14, 15 };
		int steps = sizeof( ramp ) / sizeof( ramp[0] );
		double black = CarrierLevel( &databuffer[stride*0] );
		for( i = 0; i < steps; i++ )
		{
			WriteGray( black * ( steps - i ) / ( steps + 1 ), &databuffer[stride*ramp[i]] );
		}

		WriteSignal( 1.0, 0.0, 0.7, 0.0, debug, &databuffer[stride*16], 0xffffffff ); //No colorburst, the back porch just stays black.
	}
	else
	{
//BTW
		WriteSignal( 0.7, 1.0, 0.9, 0.0, debug, &databuffer[stride*3], 0xffffffff ); 
		WriteSignal( 0.7, 1.0, 0.9, 0.2, debug, &databuffer[stride*4], 0xffffffff ); 
		WriteSignal( 0.7, 1.0, 0.9, 0.4, debug, &databuffer[stride*5], 0xffffffff ); 
		WriteSignal( 0.7, 1.0, 0.9, 0.6, debug, &databuffer[stride*6], 0xffffffff ); 
		WriteSignal( 0.7, 1.0, 0.9, 0.8, debug, &databuffer[stride*7], 0xffffffff ); 
//WTB
		WriteSignal( 0.4, 0.5, 0.65, 0.0, debug, &databuffer[stride*9], 0xffffffff ); 
//WHITE
		WriteSignal( 0.5, 0.5, 0.8, 0.0, debug, &databuffer[stride*11], 0xffffffff ); 
		WriteSignal( 0.5, 0.5, 0.8, 0.2, debug, &databuffer[stride*12], 0xffffffff ); 
		WriteSignal( 0.5, 0.5, 0.8, 0.4, debug, &databuffer[stride*13], 0xffffffff ); 
		WriteSignal( 0.5, 0.5, 0.8, 0.6, debug, &databuffer[stride*14], 0xffffffff ); 
		WriteSignal( 0.5, 0.5, 0.8, 0.8, debug, &databuffer[stride*15], 0xffffffff ); 

		WriteSignal( 1.2, 0.3, 0.6, 0.0, debug, &databuffer[stride*16], 0xffffffff ); //Chroma.
	}

	WriteSignal( 1.0, 0.0, 0.0, 0.0, debug, &databuffer[stride*17], 0xffffffff ); //Sync Tip.  //-16.3 db
}

void PrintTable( FILE * f, uint32_t * databuffer, int stride )
{
	int i;
	fprintf( f, "uint32_t premodulated_table[%d] = {", stride * TABLESIZE );
	for( i = 0; i < TABLESIZE*stride; i++ )
	{
		int imod = i % TABLESIZE;
		int idiv = i / TABLESIZE;

//Transposition makes selecting colors easier, but more difficult to get stripes.  Need to test performance.

		//idiv ^= 1; //Invert rows... So we flip our bit orders.  This looks weird, but it fixes our order-of-text.
		uint32_t val = databuffer[imod * stride + idiv];

		if( imod == 0 ) { fprintf( f, "\n\t" ); }
		fprintf( f, "0x%02x, ", (val) );
	}
	fprintf( f, "\n};\n" );
}

int main()
{
	int stride = (samples+overshoot)/32;

	uint32_t databuffer[stride*TABLESIZE];

	//Both tables go in the file, the firmware picks one at compile time (OPTS += -DMONOCHROME in user.cfg)
	FILE * f = fopen( "broadcast_tables.c", "w" );
	fprintf( f, "#include \"broadcast_tables.h\"\n\n" );

	fprintf( f, "#ifdef MONOCHROME\n\n" );
	memset( databuffer, 0, sizeof( databuffer ) );
	WriteTable( databuffer, stride, 1 );
	PrintTable( f, databuffer, stride );

	fprintf( f, "\n#else\n\n" );
	memset( databuffer, 0, sizeof( databuffer ) );
	WriteTable( databuffer, stride, 0 );
	PrintTable( f, databuffer, stride );

	fprintf( f, "\n#endif\n" );
	fclose( f );

	f = fopen( "broadcast_tables.h", "w" );
	fprintf( f, "#include <c_types.h>\n\n" );
	fprintf( f, "#include <esp82xxutil.h>\n\n" );

	fprintf( f, "#define PREMOD_ENTRIES %d\n", samples/32 );
	fprintf( f, "#define PREMOD_ENTRIES_WITH_SPILL %d\n", (samples+overshoot)/32 );
	fprintf( f, "#define PREMOD_SIZE %d\n", TABLESIZE );
	fprintf( f, "#define SYNC_LEVEL 17\n" );
	fprintf( f, "#define COLORBURST_LEVEL 16\n" );
	fprintf( f, "#define BLACK_LEVEL 0\n" );
	fprintf( f, "#define GRAY_LEVEL 1\n" );
	fprintf( f, "#define WHITE_LEVEL 10\n" );
	fprintf( f, "\n" );
	fprintf( f, "extern uint32_t premodulated_table[%d];\n\n", stride * TABLESIZE );
	fclose( f );
	
	return 0;
}
