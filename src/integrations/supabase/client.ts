// This file is automatically generated. Do not edit it directly.
import { createClient } from '@supabase/supabase-js';
import type { Database } from './types';

const SUPABASE_URL = "https://dwildmlykzmdwpraehnc.supabase.co";
const SUPABASE_PUBLISHABLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR3aWxkbWx5a3ptZHdwcmFlaG5jIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzk2MjMwNjMsImV4cCI6MjA1NTE5OTA2M30.po7LkU90zA2rSccV_IMavwaLN8WqhL4USO27fr8aPp8";

// Import the supabase client like this:
// import { supabase } from "@/integrations/supabase/client";

export const supabase = createClient<Database>(SUPABASE_URL, SUPABASE_PUBLISHABLE_KEY);