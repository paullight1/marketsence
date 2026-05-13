export interface Product {
  id: string;
  name: string;
  category: string;
  brand: string;
  avgPrice: number;
  minPrice: number;
  maxPrice: number;
  listingsCount: number;
  lastUpdated: string;
}

export interface Supplier {
  id: string;
  name: string;
  source: string;
  location: string;
  trustScore: number;
  totalListings: number;
  avgPrice: number;
  suspiciousCount: number;
}

export interface PriceListing {
  id: string;
  productName: string;
  price: number;
  seller: string;
  source: string;
  location: string;
  date: string;
  isSuspicious: boolean;
}

export interface DashboardStats {
  totalProducts: number;
  totalSuppliers: number;
  totalListings: number;
  suspiciousPrices: number;
  avgTrustScore: number;
  normalizationRate: number; // The "Interview Winner" stat
}

export const categories = [
  "Construction",
  "Electronics",
  "Phones & Tablets",
  "Food & Agriculture",
  "Automotive",
  "Home & Garden",
];

export const sources = ["Jiji", "Konga", "Jumia", "Facebook", "Manual"];

export const locations = [
  "Lagos",
  "Abuja",
  "Port Harcourt",
  "Ibadan",
  "Kano",
  "Enugu",
];

export const mockProducts: Product[] = [
  {
    id: "1",
    name: "Dangote Cement 50kg",
    category: "Construction",
    brand: "Dangote",
    avgPrice: 15500,
    minPrice: 15000,
    maxPrice: 16500,
    listingsCount: 45,
    lastUpdated: "2026-05-12",
  },
  {
    id: "2",
    name: "Ashaka Cement 50kg",
    category: "Construction",
    brand: "Ashaka",
    avgPrice: 14800,
    minPrice: 14500,
    maxPrice: 15500,
    listingsCount: 28,
    lastUpdated: "2026-05-12",
  },
  {
    id: "3",
    name: "iPhone 13 Pro Max",
    category: "Phones & Tablets",
    brand: "Apple",
    avgPrice: 650000,
    minPrice: 620000,
    maxPrice: 720000,
    listingsCount: 15,
    lastUpdated: "2026-05-11",
  },
  {
    id: "4",
    name: "Samsung Galaxy S24 Ultra",
    category: "Phones & Tablets",
    brand: "Samsung",
    avgPrice: 580000,
    minPrice: 550000,
    maxPrice: 650000,
    listingsCount: 22,
    lastUpdated: "2026-05-12",
  },
  {
    id: "5",
    name: "Toyota Camry 2020",
    category: "Automotive",
    brand: "Toyota",
    avgPrice: 18500000,
    minPrice: 17000000,
    maxPrice: 21000000,
    listingsCount: 8,
    lastUpdated: "2026-05-10",
  },
  {
    id: "6",
    name: "Honda Generator 2.5KVA",
    category: "Electronics",
    brand: "Honda",
    avgPrice: 185000,
    minPrice: 175000,
    maxPrice: 200000,
    listingsCount: 12,
    lastUpdated: "2026-05-12",
  },
  {
    id: "7",
    name: "Inverter Battery 200AH",
    category: "Electronics",
    brand: "Luminous",
    avgPrice: 85000,
    minPrice: 78000,
    maxPrice: 95000,
    listingsCount: 18,
    lastUpdated: "2026-05-11",
  },
  {
    id: "8",
    name: "Ceramic Floor Tiles 60x60",
    category: "Construction",
    brand: "Nigerian Tiles",
    avgPrice: 5500,
    minPrice: 5000,
    maxPrice: 6500,
    listingsCount: 35,
    lastUpdated: "2026-05-12",
  },
];

export const mockSuppliers: Supplier[] = [
  {
    id: "1",
    name: "Alhaji Ibrahim Motors",
    source: "Jiji",
    location: "Lagos",
    trustScore: 92,
    totalListings: 156,
    avgPrice: 18500000,
    suspiciousCount: 2,
  },
  {
    id: "2",
    name: "Tech Zone Nigeria",
    source: "Konga",
    location: "Abuja",
    trustScore: 88,
    totalListings: 89,
    avgPrice: 580000,
    suspiciousCount: 1,
  },
  {
    id: "3",
    name: "BuildMart Limited",
    source: "Jumia",
    location: "Lagos",
    trustScore: 95,
    totalListings: 234,
    avgPrice: 15500,
    suspiciousCount: 0,
  },
  {
    id: "4",
    name: "Prime Electronics",
    source: "Facebook",
    location: "Port Harcourt",
    trustScore: 72,
    totalListings: 45,
    avgPrice: 185000,
    suspiciousCount: 5,
  },
  {
    id: "5",
    name: "Farm Supplies NG",
    source: "Manual",
    location: "Ibadan",
    trustScore: 85,
    totalListings: 67,
    avgPrice: 45000,
    suspiciousCount: 1,
  },
];

export const mockListings: PriceListing[] = [
  {
    id: "1",
    productName: "Dangote Cement 50kg",
    price: 15500,
    seller: "BuildMart Limited",
    source: "Jumia",
    location: "Lagos",
    date: "2026-05-12",
    isSuspicious: false,
  },
  {
    id: "2",
    productName: "Dangote Cement 50kg",
    price: 15000,
    seller: "Construction Depot",
    source: "Jiji",
    location: "Abuja",
    date: "2026-05-12",
    isSuspicious: false,
  },
  {
    id: "3",
    productName: "iPhone 13 Pro Max",
    price: 650000,
    seller: "Tech Zone Nigeria",
    source: "Konga",
    location: "Abuja",
    date: "2026-05-11",
    isSuspicious: false,
  },
  {
    id: "4",
    productName: "iPhone 13 Pro Max",
    price: 450000,
    seller: "Unknown Seller",
    source: "Facebook",
    location: "Lagos",
    date: "2026-05-10",
    isSuspicious: true,
  },
  {
    id: "5",
    productName: "Honda Generator 2.5KVA",
    price: 185000,
    seller: "Prime Electronics",
    source: "Facebook",
    location: "Port Harcourt",
    date: "2026-05-12",
    isSuspicious: false,
  },
  {
    id: "6",
    productName: "Toyota Camry 2020",
    price: 12000000,
    seller: "Quick Auto Sales",
    source: "Jiji",
    location: "Lagos",
    date: "2026-05-09",
    isSuspicious: true,
  },
];

export const mockDashboardStats: DashboardStats = {
  totalProducts: 156,
  totalSuppliers: 42,
  totalListings: 1247,
  suspiciousPrices: 23,
  avgTrustScore: 84,
  normalizationRate: 92,
};

export const priceTrends = [
  { month: "Jan", cement: 15000, iphone: 680000, generator: 175000 },
  { month: "Feb", cement: 15200, iphone: 670000, generator: 178000 },
  { month: "Mar", cement: 15400, iphone: 665000, generator: 180000 },
  { month: "Apr", cement: 15300, iphone: 660000, generator: 182000 },
  { month: "May", cement: 15500, iphone: 650000, generator: 185000 },
];

export const categoryDistribution = [
  { name: "Construction", value: 35 },
  { name: "Phones & Tablets", value: 25 },
  { name: "Electronics", value: 20 },
  { name: "Automotive", value: 10 },
  { name: "Others", value: 10 },
];