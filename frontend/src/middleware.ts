import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Lock /dashboard behind subscription check
  if (pathname.startsWith('/dashboard')) {
    const subCookie = request.cookies.get('escalatepay_sub');
    const isSubscribed = subCookie && subCookie.value === 'active';

    if (!isSubscribed) {
      const pricingUrl = request.nextUrl.clone();
      pricingUrl.pathname = '/pricing';
      pricingUrl.searchParams.set('paywall', 'true');
      return NextResponse.redirect(pricingUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/dashboard'],
};
