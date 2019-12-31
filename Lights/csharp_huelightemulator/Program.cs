using System;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace HueLightEmulator
{
    class Program
    {
        static void Main(string[] args)
        {
            cHueSwitch virtHueDevice;
            try
            {
                //Create Virtual Bulbs\Switches from XML defention.                
                virtHueDevice = cHueSwitch.LoadConfigFromFile("virthueconfig.xml");
            }
            catch (Exception ex)
            {
                Console.WriteLine("Could not Create instance from XML: {0}", ex);
                //Create 5 new Virtual Bulbs\Switches, Dimmable.
                virtHueDevice = new cHueSwitch(5, true);
                //Set listing HTTP URL\PORT
                //virtHueDevice.ListenURL = "http://+:8075/";
            }

            virtHueDevice.OnSetDeviceState += virtHueDevice_OnSetDeviceState;
            virtHueDevice.OnSetDimLevel += virtHueDevice_OnSetDimLevel;
            virtHueDevice.Start();

            Console.WriteLine("Application is running until you press enter");
            Console.ReadLine();
            virtHueDevice.SaveConfig("virthueconfig.xml");
        }

        private static void virtHueDevice_OnSetDimLevel(cHueSwitch caller, int DeviceID, byte DimLevel)
        {
            Console.WriteLine("Switch: {0}, Device: {1}, Dimlevel: {2}", caller.ListenURL + caller.DeviceSubUrl , DeviceID, DimLevel);
        }

        private static void virtHueDevice_OnSetDeviceState(cHueSwitch caller, int DeviceID, bool OnState)
        {
            Console.WriteLine("Switch: {0}, Device: {1}, OnState: {2}", caller.ListenURL + caller.DeviceSubUrl, DeviceID, OnState);
        }
    }
}
