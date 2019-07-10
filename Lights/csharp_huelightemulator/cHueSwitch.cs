/*
 * 
 * Copyright 2019 - Roeland Kluit
 * 
 * This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.
 * This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. You should have received a copy of the GNU General Public License along with this program; if not, write to the Free Software Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
 * 
 * */
using System;
using System.IO;
using System.Text;
using System.Net;
using System.Threading.Tasks;
using System.Xml.Serialization;

namespace HueLightEmulator
{
    public class cHueSwitch : IDisposable
    {
        [XmlRoot(ElementName = "HueDeviceConfig")]
        public class HueDeviceConfig
        {
            [XmlElement(ElementName = "DeviceListenURL")]
            public string url { get; set; } = "http://+:80/";

            [XmlElement(ElementName = "DeviceSubDirectoryURL")]
            public string device_sub_url { get; set; } = "";

            [XmlElement(ElementName = "DeviceIsDimmable")]
            public bool DeviceDimEnabled { get; set; }

            [XmlElement(ElementName = "DeviceStatus")]
            public bool[] DeviceStatus { get; set; }

            [XmlElement(ElementName = "DeviceDimLevels")]
            public byte[] DeviceDimLevel { get; set; }
        }

        HueDeviceConfig hdc = new HueDeviceConfig();
        public delegate void EventOnSetDimlevel(cHueSwitch caller, int DeviceID, byte DimLevel);
        public delegate void EventOnSetDeviceState(cHueSwitch caller, int DeviceID, bool OnState);
        public event EventOnSetDimlevel OnSetDimLevel;
        public event EventOnSetDeviceState OnSetDeviceState;

        bool runServer = false;
        private HttpListener listener;
        private Task listenTask;
        private static string pageData =
            "<!DOCTYPE>" +
            "<html>" +
            "  <head>" +
            "    <title>HTTP Virtual Hue Lamp (ESP8266) emulated</title>" +
            "  </head>" +
            "  <body>" +
            "    <p>Devices: {0}</p>" +
            "    <p>Dimmable: {1}</p>" +
            "  </body>" +
            "</html>";

        public cHueSwitch(int DeviceCount, bool isDimmer)
        {
            hdc.DeviceStatus = new bool[DeviceCount];
            hdc.DeviceDimLevel = new byte[DeviceCount];
            hdc.DeviceDimEnabled = isDimmer;
            listener = new HttpListener();
        }

        public static cHueSwitch LoadConfigFromFile(string filename)
        {
            try
            {
                var serializer = new XmlSerializer(typeof(HueDeviceConfig));
                using (StreamReader textReader = new StreamReader(filename))
                {
                    string XML = textReader.ReadToEnd();
                    return new cHueSwitch(XML);

                }
            }
            catch (Exception e)
            {
                throw new Exception("Unable to read configuration", e);
            }
        }

        public bool SaveConfig(string filename)
        {
            try
            {
                var serializer = new XmlSerializer(typeof(HueDeviceConfig));
                using (TextWriter textWriter = new StreamWriter(filename))
                {
                    serializer.Serialize(textWriter, hdc);
                    textWriter.Close();
                    return true;
                }
            }
            catch
            {
                return false;
            }
        }

        public cHueSwitch(string XML)
        {
            var serializer = new XmlSerializer(typeof(HueDeviceConfig));
            using (StringReader textReader = new StringReader(XML))
            {
                hdc = (HueDeviceConfig)serializer.Deserialize(textReader);
                if (hdc.DeviceStatus.Length != hdc.DeviceDimLevel.Length)
                {
                    throw new Exception("Array Lenght Mismatch");
                }
            }
            listener = new HttpListener();
        }

        public string GetConfig()
        {            
            var serializer = new XmlSerializer(typeof(HueDeviceConfig));
            using (StringWriter textWriter = new StringWriter())
            {
                serializer.Serialize(textWriter, hdc);
                return textWriter.ToString();
            }
        }

        public bool SetConfig(string XML)
        {
            try
            {
                HueDeviceConfig lhdc = new HueDeviceConfig();
                var serializer = new XmlSerializer(typeof(HueDeviceConfig));
                using (StringReader textReader = new StringReader(XML))
                {
                    lhdc = (HueDeviceConfig)serializer.Deserialize(textReader);
                    if (hdc.DeviceStatus.Length == lhdc.DeviceStatus.Length && lhdc.DeviceDimLevel.Length == lhdc.DeviceDimLevel.Length)
                    {
                        hdc = lhdc;
                        return true;
                    }
                }
                return false;
            }
            catch
            {
                return false;
            }
        }

        public bool Start(bool silent = false)
        {
            try
            {
                if (!listener.IsListening)
                {
                    if (hdc.device_sub_url != "" && !hdc.device_sub_url.EndsWith("/"))
                    {
                        hdc.device_sub_url = hdc.device_sub_url + "/";
                    }
                    runServer = true;
                    listener.Prefixes.Clear();
                    listener.Prefixes.Add(ListenURL + hdc.device_sub_url);
                    listener.Start();
                    if (!silent)
                        Console.WriteLine("Listening for connections on {0}", ListenURL + hdc.device_sub_url);

                    // Handle requests
                    listenTask = HandleIncomingConnections();
                    return true;
                }
                return false;
            }
            catch(Exception ex)
            {
                    throw new Exception("Unable to start module", ex);
            }
        }

        public bool Stop()
        {
            if (listener.IsListening)
            {
                runServer = false;
                listener.Stop();
                return true;
            }
            return false;
        }

        public bool SetState(int DeviceNumber, bool isOn, byte dimLevel)
        {
            try
            {
                hdc.DeviceStatus[DeviceNumber - 1] = isOn;
                hdc.DeviceDimLevel[DeviceNumber - 1] = dimLevel;
                return true;
            }
            catch
            {
                return false;
            }
        }

        public bool SetOnState(int DeviceNumber, bool isOn)
        {
            try
            {
                hdc.DeviceStatus[DeviceNumber - 1] = isOn;
                return true;
            }
            catch
            {
                return false;
            }
        }

        public byte GetDimState(int DeviceNumber)
        {
            try
            {
                return hdc.DeviceDimLevel[DeviceNumber - 1];
            }
            catch
            {
                throw new Exception("Unable to retrieve value");
            }
        }

        public bool GetOnState(int DeviceNumber)
        {
            try
            {
                return hdc.DeviceStatus[DeviceNumber - 1];
            }
            catch
            {
                throw new Exception("Unable to retrieve value");
            }
        }

        public bool SetDimState(int DeviceNumber, byte dimLevel)
        {
            try
            {
                hdc.DeviceDimLevel[DeviceNumber - 1] = dimLevel;
                return true;
            }
            catch
            {
                return false;
            }
        }

        public bool isRunning
        {
            get
            {
                try
                {
                    if (listenTask.Status == TaskStatus.Faulted || listenTask.Status == TaskStatus.RanToCompletion)
                        return false;
                    else
                        return true;
                }
                catch
                {
                    return false;
                }
            }
        }

        public TaskStatus Status
        {
            get
            {
                if (listenTask == null)
                    return TaskStatus.WaitingToRun;
                else
                    return listenTask.Status;
            }
        }

        public string ListenURL
        {
            get
            {
                return hdc.url;
            }

            set
            {
                hdc.url = value;
            }
        }

        public string DeviceSubUrl
        {
            get
            {
                return hdc.device_sub_url;
            }

            set
            {
                hdc.device_sub_url = value;
            }
        }

        public void Dispose()
        {
            runServer = false;
            listener.Close();
        }

        private int? GetDeviceIDFromRequest(HttpListenerRequest req)
        {
            if (req.QueryString["light"] != null)
            {
                try
                {
                    int lamp = int.Parse(req.QueryString["light"]) - 1;
                    if (lamp > hdc.DeviceStatus.Length - 1)
                    {
                        return null;
                    }
                    return lamp;
                }
                catch
                {
                    return null;
                }
            }
            return null;
        }

        private bool? GetOnStateFromRequest(HttpListenerRequest req)
        {
            if (req.QueryString["on"] != null)
            {
                try
                {
                    return bool.Parse(req.QueryString["on"]);
                }
                catch
                {
                    return null;
                }
            }
            return null;
        }

        private byte? GetBrighnessFromRequest(HttpListenerRequest req)
        {
            if (req.QueryString["bri"] != null)
            {
                try
                {
                    return byte.Parse(req.QueryString["bri"]);
                }
                catch
                {
                    return null;
                }
            }
            return null;
        }

        private async Task HandleIncomingConnections()
        {         
            while (runServer)
            {
                // Will wait here until we hear from a connection
                HttpListenerContext httpContext = await listener.GetContextAsync();

                // Peel out the requests and response objects
                HttpListenerRequest httpRequest = httpContext.Request;
                HttpListenerResponse httpResponse = httpContext.Response;
                
                byte[] data = new byte[0];

                //Detect URL requested
                if (httpRequest.Url.AbsolutePath == "/" + hdc.device_sub_url + "detect")
                {
                    if (hdc.DeviceDimEnabled)
                        data = Encoding.UTF8.GetBytes("{\"hue\": \"bulb\",\"lights\": " + hdc.DeviceStatus.Length + ",\"name\": \"Virtual Dimmable Switch\",\"modelid\": \"LWB010\",\"mac\": \"25:35:e4:35:fe:18\"}");
                    else
                        data = Encoding.UTF8.GetBytes("{\"hue\": \"bulb\",\"lights\": " + hdc.DeviceStatus.Length + ",\"name\": \"Virtual Switch\",\"modelid\": \"Virtual Switch\",\"mac\": \"25:35:d4:34:fe:28\"}");
                }
                //Get status
                else if (httpRequest.Url.AbsolutePath == "/" + hdc.device_sub_url + "get")
                {
                    int? lamp;
                    if ((lamp = GetDeviceIDFromRequest(httpRequest)) != null)
                    {
                        if (hdc.DeviceDimEnabled)
                            data = Encoding.UTF8.GetBytes("{\"on\": " + hdc.DeviceStatus[(int)lamp].ToString().ToLower() + ", \"bri\":" + hdc.DeviceDimLevel[(int)lamp] + "}");
                        else
                            data = Encoding.UTF8.GetBytes("{\"on\": " + hdc.DeviceStatus[(int)lamp].ToString().ToLower() + " }");
                    }
                    else
                    {
                        data = Encoding.UTF8.GetBytes("Error, light missing or invalid");
                    }
                }
                //Set device
                else if (httpRequest.Url.AbsolutePath == "/" + hdc.device_sub_url + "set")
                {
                    int? lamp;
                    byte? bri;
                    bool? onState;
                    if ((lamp = GetDeviceIDFromRequest(httpRequest)) != null)
                    {
                        if ((onState = GetOnStateFromRequest(httpRequest)) != null)
                        {
                            hdc.DeviceStatus[(int)lamp] = (bool)onState;
                            OnSetDeviceState?.Invoke(this, (int)lamp + 1, (bool)onState);
                        }

                        if ((bri = GetBrighnessFromRequest(httpRequest)) != null)
                        {
                            hdc.DeviceDimLevel[(int)lamp] = (byte)bri;
                            OnSetDimLevel?.Invoke(this, (int)lamp + 1, (byte)bri);
                        }

                        if (hdc.DeviceDimEnabled)
                            data = Encoding.UTF8.GetBytes("OK, bri: " + hdc.DeviceDimLevel[(int)lamp] + ", state: " + hdc.DeviceStatus[(int)lamp].ToString().ToLower());
                        else
                            data = Encoding.UTF8.GetBytes("OK, state: " + hdc.DeviceStatus[(int)lamp].ToString().ToLower());
                    }
                    else
                    {
                        data = Encoding.UTF8.GetBytes("Error, light missing or invalid");
                    }
                }
                else
                {
                    data = Encoding.UTF8.GetBytes(String.Format(pageData, this.hdc.DeviceStatus.Length, hdc.DeviceDimEnabled.ToString()));
                }

                httpResponse.ContentType = "text/html";
                httpResponse.ContentEncoding = Encoding.UTF8;
                httpResponse.ContentLength64 = data.LongLength;
                await httpResponse.OutputStream.WriteAsync(data, 0, data.Length);
                httpResponse.Close();                
            }
        }
    }
}
