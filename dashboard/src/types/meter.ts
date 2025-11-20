export interface MeterReading {
  time: string;
  value: number;
  confidence: 'high' | 'medium' | 'low';
  meterType: 'water' | 'electric' | 'gas';
}

// Meter data interface for display
export interface MeterData {
  current: number;
  unit: string;
  lastUpdated: string;
  confidence: 'high' | 'medium' | 'low';
  change24h: number;
  trend: 'up' | 'down' | 'stable';
}

export interface MeterStats {
  water: MeterData;
  electric: MeterData;
  gas: MeterData;
}

export interface ChartDataPoint {
  timestamp: string;
  value: number;
}

export interface CostData {
  meterType: 'water' | 'electric' | 'gas';
  dailyCost: number;
  monthlyCost: number;
  currency: string;
}

// Meter display configuration
export interface MeterDisplayConfig {
  icon: string;
  label: string;
  color: string;
  lightColor: string;
  darkColor: string;
  unit: string;
}

// Meter configuration from backend
export interface MeterConfig {
  name: string;
  type: 'water' | 'electric' | 'gas';
  display: MeterDisplayConfig;
  reading_interval: number;
  camera_ip: string;
}

// Pricing configuration interfaces
export interface WaterPricing {
  provider: string;
  volumetric_rate: {
    water: number;
    wastewater: number;
    stormwater: number;
    unit: string;
    notes: string;
  };
  fixed_charges: {
    monthly_service_charge: number;
    unit: string;
  };
  minimum_usage: {
    amount: number;
    unit: string;
  };
  tiered_pricing: boolean;
}

export interface ElectricityPricing {
  provider: string;
  rate_plan: string;
  effective_date: string;
  time_of_use_rates: {
    off_peak: { rate: number; unit: string };
    mid_peak: { rate: number; unit: string };
    on_peak: { rate: number; unit: string };
  };
  delivery_charges: {
    monthly_service_charge: number;
    distribution_volumetric_charge: number;
    transmission_charge: number;
    unit: string;
    notes: string;
  };
  rebates_and_taxes: {
    ontario_electricity_rebate: {
      rate: number;
      unit: string;
      effective_date: string;
      applies_to: string;
    };
    hst: {
      rate: number;
      unit: string;
      applies_to: string;
    };
  };
}

export interface GasPricing {
  provider: string;
  rate_zone: string;
  effective_date: string;
  gas_supply: {
    commodity_charge: number;
    gas_cost_adjustment: number;
    rate_adjustment: number;
    total_effective_rate: number;
    unit: string;
    notes: string;
  };
  delivery_charges: {
    volumetric_charge: number;
    unit: string;
  };
  transportation_charges: {
    volumetric_charge: number;
    unit: string;
  };
  fixed_charges: {
    monthly_customer_charge: number;
    unit: string;
  };
  carbon_charges: {
    federal_carbon_charge: {
      rate: number;
      unit: string;
      notes: string;
    };
    facility_carbon_charge: {
      rate: number;
      unit: string;
    };
  };
}

export interface PricingConfig {
  metadata: {
    location: string;
    effective_date: string;
    last_updated: string;
    currency: string;
    notes: string;
  };
  water: WaterPricing;
  electricity: ElectricityPricing;
  natural_gas: GasPricing;
}

export interface HouseholdConfig {
  address: {
    street: string;
    city: string;
    province: string;
    postal_code: string;
    country: string;
  };
  timezone: string;
}
