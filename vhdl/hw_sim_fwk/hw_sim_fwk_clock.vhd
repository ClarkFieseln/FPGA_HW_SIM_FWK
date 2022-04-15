
library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use STD.textio.all;
use ieee.std_logic_textio.all;
library hw_sim_fwk;
use hw_sim_fwk.hw_sim_fwk_common.all;

-- Note: the followig metacomment is not part of the VHDL synthesis standard (IEEE P1076.6) so behavior is tool dependent.
-- synthesis translate_off
-- ######################
-- NOTE: add this module to hw_sim_fwk library in your project, and associate it only with Simulation.

entity hw_sim_fwk_clock is
    generic(
        FILE_PATH                 : string  := "/tmp/";
        CLOCK_FILE_NAME           : string  := "/tmp/clock_high"; -- FILE_PATH & "clock_high" -- cannot use concatenation here!
        CLOCK_PERIOD              : time    := 20 ns;
        -- Note: 50000000 works fine with CLOCK_PERIOD = 20ns and CLOCK_PERIOD_EXTERNAL = 1sec
        --       according to the formula CLOCK_PERIOD_EXTERNAL/CLOCK_PERIOD both in units of ns
        MAX_ELAPSED_CLOCK_PERIODS : integer := 50000000;
        PROTOCOL_CLOCK            : boolean := false -- to report details
    );
    port(
        hw_clock : out std_logic
    );
end hw_sim_fwk_clock;

architecture arch of hw_sim_fwk_clock is
begin
    -- polling process
    -- ###############
    proc_update_clock : process
        variable pos_edge            : boolean := false;
        variable elapsed_clk_periods : integer := 0;
        variable elapsed_checks      : integer := 0;
        variable initialized         : boolean := false;
    begin
        elapsed_clk_periods := elapsed_clk_periods + 1;
        -- initialization?
        if initialized = false then
            initialized := true;
            -- initialize clock signal depending on file existence
            if (file_exists(CLOCK_FILE_NAME) = true) then
                hw_clock <= '1';
                pos_edge := true;
                -- if (PROTOCOL_CLOCK = true) then
                report "hw_clock initialized to 1";
                -- end if;
            else
                hw_clock <= '0';
                pos_edge := false;
                -- if (PROTOCOL_CLOCK = true) then
                report "hw_clock initialized to 0";
                -- end if;
            end if;
        -- check for rising-edge, now or later?
        -- NOTE: although this avoids checking permanently (and probably blocking) the input file
        --       it does not avoid looping "without pause" and thus consuming 100% of a CPU-Core!
        -- TODO: find out if it is possible somehow to pause/sleep between external clock cycles
        --       but "without resuming simulation".
        elsif (elapsed_clk_periods = MAX_ELAPSED_CLOCK_PERIODS) then
            elapsed_clk_periods := 0;
            elapsed_checks      := elapsed_checks + 1;
            if (PROTOCOL_CLOCK = true) then
                report "checking clk_rising_edge..";
            end if;
            -- file clock H exists:
            if (file_exists(CLOCK_FILE_NAME) = true) then
                -- otherwise we generate additional clock cycles which do not correspond with external GUI simulation
                -- rising edge?
                if pos_edge = false then
                    if (PROTOCOL_CLOCK = true) then
                        report "Nr of checks until clk_rising_ege = " & integer'image(elapsed_checks);
                    end if;
                    elapsed_checks := 0;
                    pos_edge       := true;
                    hw_clock       <= '1';
                    wait for CLOCK_PERIOD / 2;
                end if;
            -- file clock H does not exist:
            else
                -- falling edge?
                if pos_edge = true then
                    pos_edge := false;
                    hw_clock <= '0';
                    wait for CLOCK_PERIOD / 2;
                end if;
            end if;
        end if;
    end process proc_update_clock;
end arch;

-- synthesis translate_on
-- ######################

