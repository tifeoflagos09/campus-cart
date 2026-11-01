# CampusCart 🛒
### Your Campus, Your Essentials

## Overview

CampusCart is a campus shopping platform built with Python and Streamlit. It provides students with a convenient way to browse products and services offered by campus vendors, add items to a shopping cart, and complete a simulated checkout.

The application also helps demonstrate how vendors can manage product availability, monitor stock levels, and handle orders through a simple digital shopping experience.

## The Problem

Students often have to visit different vendors or ask around to find products and services available on campus. They may need to confirm prices, check availability, and arrange purchases manually.

For campus vendors, managing products, tracking stock, and keeping records of sales can also become difficult when handled manually.

## The Solution

CampusCart brings campus shopping into one platform.

Students can browse available products, search by name, filter by category, add items to their cart, and complete a checkout process.

The application also includes inventory checks, expiry-date validation, pricing rules, simulated payment methods, and transaction receipts.

## Target Users

- **Students:** People who need convenient access to everyday campus products and services.
- **Campus vendors:** Sellers who provide products and services to students.
- **Student-run businesses:** Small businesses operating within campus communities.

## Key Features

- **Product catalogue:** Browse products across different categories.
- **Product search:** Find products by name.
- **Category filtering:** Explore products by category.
- **Price sorting:** Sort products based on price.
- **Shopping cart:** Add products, adjust quantities, and remove items.
- **Automatic discounts:** Apply eligible discounts during checkout.
- **Coupon codes:** Redeem supported promotional codes.
- **Inventory management:** Track product quantities and prevent purchases beyond available stock.
- **Expiry-date validation:** Prevent expired perishable products from being purchased.
- **Multiple payment options:** Demonstrate cash, card, and mobile money payment flows.
- **Order receipts:** View and download transaction receipts.
- **Transaction summary:** Review completed transactions within the active session.

## Product Categories

CampusCart includes sample products and services across five categories:

1. Stationery
2. Campus merchandise
3. Tech accessories
4. Food and drinks
5. Digital services

## Pricing and Checkout Rules

The application demonstrates the following pricing rules:

- **Automatic discount:** 10% discount on qualifying orders with a subtotal above ₦2,000.
- **Coupon discount:** The `CAMPUS15` coupon provides 15% off qualifying orders with a subtotal of at least ₦5,000.
- **Discount interaction:** When the coupon is applied, it replaces the automatic discount.
- **Campus delivery:** A demonstration delivery fee of ₦500 applies when campus delivery is selected.
- **Pickup:** Free pickup option.
- **Digital services:** Digital-only orders do not attract a delivery fee.

## Technology Stack

- **Python:** Core application logic and business rules.
- **Streamlit:** Web application interface.
- **Object-Oriented Programming:** Product, cart, inventory, and payment models.
- **Python unittest:** Automated testing.

## Project Structure

```text
campus-cart/
│
├── app.py
├── catalog.py
├── models/
├── utils/
├── tests/
├── requirements.txt
└── README.md
```

## Getting Started

Follow these steps to run CampusCart locally.

### Prerequisites

- Python installed on your computer.
- Git installed on your computer.
- A terminal or command prompt.

### 1. Clone the repository

```bash
git clone https://github.com/tifeoflagos09/campus-cart.git
```

### 2. Enter the project directory

```bash
cd campus-cart
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment

For Windows:

```bash
.venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the application

```bash
streamlit run app.py
```

The application should open in your browser. If it does not, Streamlit will provide a local URL in your terminal.

## Running the Tests

CampusCart includes automated tests for important application functionality, including product expiry, inventory, shopping cart operations, pricing, payments, and receipts.

Run the test suite using:

```bash
python -m unittest discover -s tests -v
```

**Latest local test result:** 59 tests passed.

## Current Limitations

CampusCart is a capstone demonstration project. Some features are simulated rather than connected to live services.

- Payments are simulated; no real money is collected.
- Product, cart, and transaction data are held within the active browser session.
- The product catalogue contains sample data.
- Digital services are represented through vouchers rather than live service fulfilment.
- Delivery is demonstrated through a checkout fee; there is no live delivery integration.

## Future Improvements

Possible improvements include:

- Database integration for persistent product, customer, and order records.
- Vendor dashboards for managing products and sales.
- User registration and authentication.
- Integration with a real payment gateway.
- Order tracking and customer notifications.
- Live campus delivery coordination.
- Product images and richer product descriptions.
- Deployment for access beyond a local development environment.

## Author

**Boluwatife Ajose**

Developed as a capstone project through the DataEpic Mentorship Program.


