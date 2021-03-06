﻿// <copyright file="Settings.cs" company="Cirrious">
// (c) Copyright Cirrious. http://www.cirrious.com
// This source is subject to the Microsoft Public License (Ms-PL)
// Please see license.txt on http://opensource.org/licenses/ms-pl.html
// All other rights reserved.
// </copyright>
//  
// Project Lead - Stuart Lodge, Cirrious. http://www.cirrious.com - Hire me - I'm worth it!

namespace Cirrious.MvvmCross.Plugins.Settings.Touch
{
    public class Settings : ISettings
    {
        public bool CanShow(string which)
        {
            // TODO
            switch (which)
            {
                case KnownSettings.Bluetooth:
                case KnownSettings.Wifi:
                    return false;
            }

            return false;
        }

        public void Show(string which)
        {
            // TODO
        }
    }
}