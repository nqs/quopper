﻿// <copyright file="ISpeechListener.cs" company="Cirrious">
// (c) Copyright Cirrious. http://www.cirrious.com
// This source is subject to the Microsoft Public License (Ms-PL)
// Please see license.txt on http://opensource.org/licenses/ms-pl.html
// All other rights reserved.
// </copyright>
//  
// Project Lead - Stuart Lodge, Cirrious. http://www.cirrious.com - Hire me - I'm worth it!

using System;
using System.Collections.Generic;
using Cirrious.MvvmCross.Platform;

namespace Cirrious.MvvmCross.Plugins.Speech
{
    public interface ISpeechListener
    {
        void Start(IList<string> words);
        void Stop();
        event EventHandler<MvxValueEventArgs<PossibleWord>> Heard;
    }
}