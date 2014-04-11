// <copyright file="StreamSocketWrapper.cs" company="Cirrious">
// (c) Copyright Cirrious. http://www.cirrious.com
// This source is subject to the Microsoft Public License (Ms-PL)
// Please see license.txt on http://opensource.org/licenses/ms-pl.html
// All other rights reserved.
// </copyright>
//  
// Project Lead - Stuart Lodge, Cirrious. http://www.cirrious.com - Hire me - I'm worth it!

using System;
using System.Threading.Tasks;
using Cirrious.MvvmCross.Plugins.Sphero.HackFileShare;
using Windows.Networking.Sockets;
using Windows.Storage.Streams;

namespace Cirrious.MvvmCross.Plugins.Sphero.WinRT.Tooth
{
    public class StreamSocketWrapper : IStreamSocketWrapper, IDisposable
    {
        public StreamSocketWrapper()
        {
        }

        public async Task<byte> ReceiveByte()
        {
            byte[] buffer = null;

            while (buffer == null)
            {
                try
                {
                    buffer = HackSingleton.Instance.Service.ReceiveFromSphero(1);
                }
                catch (Exception exception)
                {
                    throw new SpheroPluginException(exception, "Read failed - suspect disconnected");
                }
            }

            var x = buffer[0];
            return x;
        }

        public async Task SendBytes(byte[] payload)
        {
            HackSingleton.Instance.Service.SendToSphero(payload);
        }

        public void Dispose()
        {
            Dispose(true);
        }

        protected virtual void Dispose(bool isDisposing)
        {
            if (isDisposing)
            {
                // nothing to do
            }
        }
    }
}