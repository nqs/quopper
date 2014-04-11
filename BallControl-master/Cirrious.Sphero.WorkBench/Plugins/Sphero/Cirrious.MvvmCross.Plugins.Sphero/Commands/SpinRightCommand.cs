﻿// <copyright file="SpinRightCommand.cs" company="Cirrious">
// (c) Copyright Cirrious. http://www.cirrious.com
// This source is subject to the Microsoft Public License (Ms-PL)
// Please see license.txt on http://opensource.org/licenses/ms-pl.html
// All other rights reserved.
// </copyright>
//  
// Project Lead - Stuart Lodge, Cirrious. http://www.cirrious.com - Hire me - I'm worth it!

namespace Cirrious.MvvmCross.Plugins.Sphero.Commands
{
    public class SpinRightCommand : RawMotorCommand
    {
        public SpinRightCommand(int spinSpeed)
            : base(RawMotorDirection.Reverse, spinSpeed, RawMotorDirection.Forward, spinSpeed)
        {
        }
    }
}