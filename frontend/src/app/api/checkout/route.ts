import { NextResponse } from 'next/server';
import Stripe from 'stripe';

export async function POST(request: Request) {
  try {
    const body = await request.json().catch(() => ({}));
    const stripeKey = process.env.STRIPE_SECRET_KEY;

    // If real Stripe credentials configured, initiate real Stripe Checkout session
    if (stripeKey && !stripeKey.includes('your_stripe')) {
      const stripe = new Stripe(stripeKey, { apiVersion: '2024-06-20' as any });
      const origin = request.headers.get('origin') || 'http://localhost:3000';

      const session = await stripe.checkout.sessions.create({
        payment_method_types: ['card'],
        line_items: [
          {
            price_data: {
              currency: 'usd',
              product_data: {
                name: 'Pro Automation Plan - EscalatePay',
                description: 'Autonomous 6-Hour Escalation Sweeps, Multi-Tier HTML Templates, Stripe Sync.',
              },
              unit_amount: 2900, // $29.00
              recurring: {
                interval: 'month',
              },
            },
            quantity: 1,
          },
        ],
        mode: 'subscription',
        subscription_data: {
          trial_period_days: 14,
        },
        success_url: `${origin}/dashboard?session_id={CHECKOUT_SESSION_ID}&subscribed=true`,
        cancel_url: `${origin}/pricing?cancelled=true`,
      });

      const response = NextResponse.json({ url: session.url, session_id: session.id });
      // Set active subscription cookie
      response.cookies.set('escalatepay_sub', 'active', {
        path: '/',
        maxAge: 60 * 60 * 24 * 30, // 30 days
        sameSite: 'lax',
      });
      return response;
    }

    // Development / Mock Checkout Activation
    const response = NextResponse.json({
      status: 'active',
      plan: 'Pro Automation Plan',
      trial_days: 14,
      amount: '$29/mo',
      url: '/dashboard?subscribed=true',
    });

    response.cookies.set('escalatepay_sub', 'active', {
      path: '/',
      maxAge: 60 * 60 * 24 * 30, // 30 days
      sameSite: 'lax',
    });

    return response;
  } catch (error: any) {
    console.error('Checkout error:', error);
    return NextResponse.json({ error: error.message || 'Internal error' }, { status: 500 });
  }
}
