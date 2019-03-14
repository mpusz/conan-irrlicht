#include <irrlicht.h>

using namespace irr;

#ifdef _MSC_VER
#pragma comment(lib, "Irrlicht.lib")
#endif

int main()
{
	// create device
	IrrlichtDevice *device = createDevice(video::EDT_NULL, core::dimension2d<u32>(640, 480), 16, false);
	if (device == 0)
		return 1; // could not create selected driver.
	device->drop();

	return 0;
}
