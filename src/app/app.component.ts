import { Component } from '@angular/core';

@Component({
  selector: 'app-root',
  standalone: true,
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  readonly productName = 'PricePilot Next';

  readonly features = [
    {
      title: 'Competitor price scanner',
      description: 'Tracks nearby competitor prices every morning and flags opportunities to adjust margins safely.'
    },
    {
      title: 'Demand-aware recommendations',
      description: 'Uses sales velocity, weather, and local events to suggest daily price updates by SKU tier.'
    },
    {
      title: 'One-click POS export',
      description: 'Sends approved price updates to common POS systems without spreadsheet work.'
    }
  ];

  readonly monetization = [
    'Starter: $149/month for up to 3,000 SKUs',
    'Growth: $399/month for up to 15,000 SKUs + multi-store analytics',
    'Performance add-on: 1% of verified incremental gross profit'
  ];
}
