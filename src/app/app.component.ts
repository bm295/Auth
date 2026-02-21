import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  standalone: true,
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  readonly serviceName = 'ClipForge Studio';

  readonly highlights = [
    {
      title: 'Auto-cut by story beat',
      description: 'Upload long footage and get tight shorts automatically segmented around hooks, transitions, and payoff moments.'
    },
    {
      title: 'Platform-native outputs',
      description: 'Deliver optimized versions for TikTok, Reels, and Shorts with safe zones, captions, and pacing tuned per platform.'
    },
    {
      title: 'Creator growth toolkit',
      description: 'Generate title variants, emoji-safe subtitles, and posting suggestions to increase retention and completion rates.'
    }
  ];

  readonly workflow = [
    'Drop in raw footage, podcast episodes, webinars, or stream VODs.',
    'Select style presets: “Fast Hook”, “Educational”, or “Storytelling”.',
    'Review AI cuts, tweak captions, and export in one click.',
    'Schedule to socials or download watermark-free masters.'
  ];

  readonly pricing = [
    {
      plan: 'Starter',
      amount: '$39/mo',
      details: '30 edited clips per month, auto-captions, watermark exports'
    },
    {
      plan: 'Creator Pro',
      amount: '$99/mo',
      details: '120 clips, brand templates, trend-aware caption styles'
    },
    {
      plan: 'Agency',
      amount: '$249/mo',
      details: 'Unlimited workspaces, client approvals, priority rendering'
    }
  ];
}
