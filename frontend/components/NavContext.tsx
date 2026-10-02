'use client';

import React, { createContext, useContext, useState } from 'react';

interface NavContextType {
  isOpen: boolean;
  toggleNav: () => void;
  closeNav: () => void;
  openNav: () => void;
}

const NavContext = createContext<NavContextType>({
  isOpen: false,
  toggleNav: () => {},
  closeNav: () => {},
  openNav: () => {},
});

export function NavProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  const toggleNav = () => setIsOpen((prev) => !prev);
  const closeNav = () => setIsOpen(false);
  const openNav = () => setIsOpen(true);

  return (
    <NavContext.Provider value={{ isOpen, toggleNav, closeNav, openNav }}>
      {children}
    </NavContext.Provider>
  );
}

export function useNav() {
  return useContext(NavContext);
}
