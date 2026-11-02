module apb_pwm (
    input wire pclk, preset_n, psel, penable, pwrite,
    input wire [7:0] paddr,
    input wire [31:0] pwdata,
    output wire pready,
    output wire pslverr,
    output reg [31:0] prdata,
    output wire pwm
);
    reg enable;
    reg [8:0] duty;
    reg [7:0] count;
    wire access = psel && penable;
    wire valid_addr = (paddr == 8'h00 || paddr == 8'h04);
    assign pready = 1'b1;
    assign pslverr = access && (!valid_addr || (pwrite && paddr == 8'h04 && pwdata > 256));
    assign pwm = enable && ({1'b0,count} < duty);
    always @* begin
        case (paddr)
            8'h00: prdata = {31'b0,enable};
            8'h04: prdata = {23'b0,duty};
            default: prdata = 0;
        endcase
    end
    always @(posedge pclk or negedge preset_n) begin
        if (!preset_n) begin enable <= 0; duty <= 0; count <= 0; end
        else begin
            if (enable) count <= count + 1'b1;
            else count <= 0;
            if (access && pwrite && !pslverr) begin
                if (paddr == 8'h00) begin enable <= pwdata[0]; count <= 0; end
                if (paddr == 8'h04) begin duty <= pwdata[8:0]; count <= 0; end
            end
        end
    end
endmodule
